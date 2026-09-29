#!/usr/bin/env python3
"""Bounded-memory native-export audio QA and staged AAC replacement.
Adapted from installed podcast-trailer-editing/scripts/preview_audio.py.
Requires ffmpeg, ffprobe, numpy, soundfile. Inputs are never modified.
"""
import argparse,hashlib,json,math,os,shutil,statistics,subprocess,sys,tempfile
from fractions import Fraction
from pathlib import Path
import numpy as np
import soundfile as sf
RATE=48000


def write_new(path,value):
 with Path(path).open('x') as f: json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def capture(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-2000:])
 return p.stdout

def probe(path,ffprobe):
 return json.loads(capture([ffprobe,'-v','error','-show_streams','-show_format','-of','json',str(path)]))
def streams(p,kind):return [s for s in p['streams'] if s.get('codec_type')==kind]
def origin(s):
 if s.get('start_pts') is not None and s.get('time_base'):return Fraction(s['start_pts'])*Fraction(s['time_base'])
 return Fraction(s.get('start_time','0'))
def duration(s):
 if s.get('duration_ts') is None or not s.get('time_base'):raise ValueError('Exact stream duration_ts/time_base required')
 return Fraction(s['duration_ts'])*Fraction(s['time_base'])
def movie_timescale(video_time_base):
 """Represent both original video ticks and 48k PCM samples exactly in MP4 edits."""
 scale=math.lcm(RATE,Fraction(video_time_base).denominator)
 if not 1<=scale<=2147483647:raise ValueError('Exact MP4 movie timescale exceeds the muxer integer range')
 return scale
def metadata_checks(preview,reference,ffprobe):
 p=probe(preview,ffprobe);r=probe(reference,ffprobe);vid=streams(p,'video');aud=streams(p,'audio');ra=streams(r,'audio')
 if len(vid)!=1 or vid[0]['codec_name']!='h264':raise ValueError('One original H.264 video stream required')
 if len(ra)!=1 or not ra[0]['codec_name'].startswith('pcm_') or streams(r,'video'):raise ValueError('Reference must be one uncompressed PCM WAV audio stream')
 info=sf.info(reference)
 if info.samplerate!=RATE or info.channels!=2:raise ValueError('Reference must be native48k stereo; no reference resampling permitted')
 if len(aud)!=1:raise ValueError('Candidate must have exactly one audio stream')
 if int(aud[0].get('sample_rate',0))!=RATE or aud[0].get('channels')!=2:raise ValueError('Candidate must be48k stereo')
 vo,ao,ro=origin(vid[0]),origin(aud[0]),origin(ra[0]);rd=Fraction(info.frames,RATE);vd=duration(vid[0]);ad=duration(aud[0]);tol=Fraction(2,RATE)
 return dict(preview_probe=p,reference_probe=r,reference_frames=info.frames,reference_subtype=info.subtype,origin_check=dict(picture_seconds=float(vo),audio_seconds=float(ao),reference_seconds=float(ro),audio_minus_picture_samples=float((ao-vo)*RATE),pass_zero_origin=vo==ao==ro==0),duration_check=dict(reference_seconds=float(rd),reference_samples=info.frames,picture_seconds=float(vd),picture_exact_fraction=str(vd),picture_minus_reference_samples=float((vd-rd)*RATE),audio_seconds=float(ad),audio_exact_fraction=str(ad),audio_minus_reference_samples=float((ad-rd)*RATE),tolerance_samples=2,pass_picture=abs(vd-rd)<=tol,pass_audio=abs(ad-rd)<=tol))

def choose_windows(reference,count,maxlag,seconds):
 """One bounded activity-rich window per equal-duration bin; first/last stay near endpoints."""
 info=sf.info(reference);n=info.frames;bin_frames=4800;rms=[]
 with sf.SoundFile(reference) as f:
  while True:
   x=f.read(RATE*20,dtype='float32',always_2d=True)
   if not len(x):break
   k=len(x)//bin_frames
   if k:rms.extend(np.sqrt(np.mean(x[:k*bin_frames].reshape(k,bin_frames,2).astype('float64')**2,axis=(1,2))))
 rms=np.asarray(rms);db=20*np.log10(np.maximum(rms,1e-12));length=min(round(seconds*RATE),int(n/count*.70));bound=round(maxlag*RATE)
 if length<4800:raise ValueError('Too short for requested number of windows')
 chosen=[]
 for i in range(count):
  lo=max(bound+1,math.ceil(i*n/count));hi=min(n-bound-1,math.floor((i+1)*n/count))
  if n/RATE>60 and i==0:hi=min(hi,30*RATE)
  if n/RATE>60 and i==count-1:lo=max(lo,n-30*RATE)
  if hi-lo<length:raise ValueError('Not enough search margin for distributed windows')
  if n/RATE<=60:
   start=round((lo+hi-length)/2)
  else:
   candidates=range(math.ceil(lo/bin_frames)*bin_frames,hi-length+1,bin_frames)
   best=None
   for s in candidates:
    v=db[s//bin_frames:(s+length)//bin_frames]
    # Activity is only a search aid; cross-correlation is the actual timing evidence.
    score=float(np.mean(v>-50))-.002*abs(float(np.percentile(v,75))+20)
    if best is None or score>best[0]:best=(score,s)
   start=best[1] if best else lo
  chosen.append([start/RATE,(start+length)/RATE])
 return chosen

def validate_windows(windows,n,count,maxlag):
 if len(windows)!=count:raise ValueError(f'Exactly{count} distributed windows required')
 bound=round(maxlag*RATE);out=[];last=-1
 for i,w in enumerate(windows):
  s,e=[round(float(t)*RATE) for t in w]
  if not bound<=s<e<=n-bound or not RATE*.1<=e-s<=RATE*10:raise ValueError('Windows need100ms–10s duration and full lag margins')
  if s<last:raise ValueError('Windows must be ordered/nonoverlapping')
  if not i*n/count<=(s+e)/2<(i+1)*n/count:raise ValueError('Each window midpoint must lie in its corresponding duration bin')
  out.append((s,e));last=e
 return out,bound

def sequential_decode(path,intervals,tail_samples,ffmpeg):
 """One decode from t0 through EOF, no seek, no atrim; retain only selected intervals and rolling tail."""
 buffers=[np.empty((e-s,2),dtype='float32') for s,e in intervals];filled=[0]*len(intervals);count=0;tail=np.empty((0,2),dtype='float32');peak=0.0
 with tempfile.TemporaryFile() as err:
  cmd=[ffmpeg,'-nostdin','-v','error','-xerror','-err_detect','explode','-i',str(path),'-map','0:a:0','-vn','-c:a','pcm_f32le','-f','f32le','-']
  p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=err);pending=b''
  try:
   while True:
    raw=p.stdout.read(65536*8)
    if not raw:break
    raw=pending+raw;whole=len(raw)//8*8;pending=raw[whole:]
    x=np.frombuffer(raw[:whole],dtype='<f4').reshape(-1,2)
    if not np.isfinite(x).all():raise ValueError('Nonfinite decoded samples')
    k=len(x);peak=max(peak,float(np.max(np.abs(x))) if k else 0)
    for j,(s,e) in enumerate(intervals):
     a,b=max(s,count),min(e,count+k)
     if b>a:buffers[j][a-s:b-s]=x[a-count:b-count];filled[j]+=b-a
    tail=np.concatenate((tail,x))[-tail_samples:];count+=k
   p.stdout.close();rc=p.wait();err.seek(0);errors=err.read().decode(errors='replace')
   if rc or errors.strip():raise RuntimeError('Sequential audio decode error: '+errors[-2000:])
   if pending:raise ValueError('Incomplete interleaved PCM frame')
  except BaseException:p.kill();p.wait();raise
 return dict(samples=count,filled=filled,peak=peak,buffers=buffers,tail=tail,command=cmd,decode_error_count=0)

def correlation(ref,candidate,bound):
 a=ref.astype('float64');a-=a.mean();b=candidate.astype('float64');n=len(a);energy=float(np.dot(a,a))
 if energy/n<1e-10:return dict(status='SILENT_REFERENCE_WINDOW')
 nf=1<<(len(b)+n-2).bit_length();c=np.fft.irfft(np.fft.rfft(b,nf)*np.fft.rfft(a[::-1],nf),nf)[n-1:len(b)]
 sums=np.concatenate(([0.],np.cumsum(b)));squares=np.concatenate(([0.],np.cumsum(b*b)));moving=squares[n:]-squares[:-n]-(sums[n:]-sums[:-n])**2/n
 denom=np.sqrt(np.maximum(moving,0)*energy);coeff=np.divide(c,denom,out=np.zeros_like(c),where=denom>0);best=int(np.argmax(coeff));lag=best-bound
 return dict(lag_samples=lag,lag_ms=lag/RATE*1000,correlation=float(np.clip(coeff[best],-1,1)),search_boundary_hit=abs(lag)==bound)

def aligned_metric(ref,cand):
 x=ref.astype('float64');y=cand.astype('float64');rms=float(np.sqrt(np.mean(x*x)));xr=x-x.mean();yr=y-y.mean();den=float(np.linalg.norm(xr)*np.linalg.norm(yr));co=float(np.dot(xr,yr)/den) if den>0 else None
 gain=float(np.dot(x,y)/np.dot(x,x)) if np.dot(x,x)>0 else None
 return dict(reference_rms_dbfs=float(20*np.log10(max(rms,1e-12))),candidate_rms_dbfs=float(20*np.log10(max(float(np.sqrt(np.mean(y*y))),1e-12))),zero_lag_correlation=co,gain_db=float(20*np.log10(abs(gain))) if gain and abs(gain)>1e-12 else None)

def verify(preview,reference,args,windows):
 meta=metadata_checks(preview,reference,args.ffprobe);n=meta['reference_frames'];ivs,bound=validate_windows(windows,n,args.window_count,args.max_lag)
 tailn=min(2*RATE,n);lastn=min(4096,n)
 captures=[(s-bound,e+bound) for s,e in ivs]+[(n-tailn,n),(n-lastn,n)]
 d=sequential_decode(preview,captures,max(tailn,2048),args.ffmpeg)
 results=[]
 with sf.SoundFile(reference) as f:
  for j,(s,e) in enumerate(ivs):
   if d['filled'][j]!=len(d['buffers'][j]):results.append(dict(start_seconds=s/RATE,end_seconds=e/RATE,status='TRUNCATED_CAPTURE'));continue
   f.seek(s);x=f.read(e-s,dtype='float64',always_2d=True);y=d['buffers'][j]
   channels=[correlation(x[:,k],y[:,k],bound) for k in range(2)]
   good=all(c.get('correlation',-1)>=args.min_correlation and not c.get('search_boundary_hit',True) for c in channels)
   results.append(dict(start_seconds=s/RATE,end_seconds=e/RATE,channels=channels,pass_zero_lag=good and all(c['lag_samples']==0 for c in channels)))
  tails=[]
  for j,size in enumerate([tailn,lastn]):
   idx=len(ivs)+j;f.seek(n-size);x=f.read(size,dtype='float64',always_2d=True)
   if d['filled'][idx]!=size:tails.append(dict(samples=size,status='TRUNCATED'));continue
   ms=[aligned_metric(x[:,k],d['buffers'][idx][:,k]) for k in range(2)]
   active=any(m['reference_rms_dbfs']>-55 for m in ms)
   passed=not active or all((m['zero_lag_correlation'] or -1)>= (.97 if j==0 else .90) and m['gain_db'] is not None and abs(m['gain_db'])<=1 for m in ms)
   tails.append(dict(samples=size,start_seconds=(n-size)/RATE,end_seconds=n/RATE,channels=ms,reference_active_above_minus55_dbfs=active,pass_tail=passed,limit='Quiet tail below−55dBFS is verified by sequential count and exact coverage; its perceptual correlation is not required.'))
 codec=streams(meta['preview_probe'],'audio')[0]['codec_name'];extra=d['samples']-n
 # AAC can expose the remainder of its final1024-sample frame, but must reach every reference sample.
 allowance=1023 if codec=='aac' else 2;countok=0<=extra<=allowance
 if countok and extra:
  padding=d['tail'][-extra:];pad_rms=float(np.sqrt(np.mean(padding.astype('float64')**2)))
 else:pad_rms=None
 originok=meta['origin_check']['pass_zero_origin'];dur=meta['duration_check'];allwin=all(r.get('pass_zero_lag',False) for r in results);tailok=all(t.get('pass_tail',False) for t in tails)
 failures=[]
 if not originok:failures.append('NONZERO_OR_MISMATCHED_STREAM_ORIGIN')
 if not dur['pass_picture'] or not dur['pass_audio']:failures.append('DURATION_MISMATCH')
 if not countok:failures.append('SEQUENTIAL_SAMPLE_COUNT_OR_TAIL_MISMATCH')
 if not allwin:failures.append('NONZERO_LAG_OR_INCONCLUSIVE_WINDOW')
 if not tailok:failures.append('TAIL_SIGNAL_MISMATCH')
 return dict(status='PASS_ZERO_LAG' if not failures else'FAIL',failures=failures,preview=str(Path(preview).resolve()),reference=str(Path(reference).resolve()),sample_rate=RATE,channels=2,reference_samples=n,sequential_decoded_samples=d['samples'],decoded_extra_tail_samples=extra,allowed_extra_aac_padding_samples=allowance,no_reference_sample_truncation=countok,extra_padding_rms_dbfs=float(20*np.log10(max(pad_rms,1e-12))) if pad_rms is not None else None,origin_check=meta['origin_check'],duration_check=dur,lag_convention='Positive means candidate audio is delayed relative to native PCM.',window_count=args.window_count,min_correlation=args.min_correlation,tolerance_samples=0,windows=results,tail_checks=tails,sequential_decode_command=d['command'],decode_error_count=d['decode_error_count'],decoded_sample_peak_dbfs=float(20*np.log10(max(d['peak'],1e-12))),memory_contract='Sequential65536-frame decode chunks; only<=12×12s stereo windows,2s tail and small100ms RMS statistics retained. No full-length PCM decoding into RAM.',validation_limit='Window correlation verifies timing at distributed measured regions, not every-sample equivalence of lossy AAC. Full sequential decode verifies length and tail coverage; compressed-picture hash verifies identical payload, not source picture quality. Automatic activity windows are signal-selected candidates in this dialogue program, not semantic speech recognition.')

def video_hash(path,ffmpeg):
 return capture([ffmpeg,'-nostdin','-v','error','-i',str(path),'-map','0:v:0','-c:v','copy','-f','hash','-hash','sha256','-']).decode().strip().split('=',1)[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['verify','replace']);p.add_argument('--preview',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--out',type=Path);p.add_argument('--windows',type=Path);p.add_argument('--window-count',type=int,choices=[6,12],default=12);p.add_argument('--window-seconds',type=float,default=6);p.add_argument('--max-lag',type=float,default=.15);p.add_argument('--min-correlation',type=float,default=.97);p.add_argument('--ffmpeg',default='ffmpeg');p.add_argument('--ffprobe',default='ffprobe');a=p.parse_args()
 for tool in[a.ffmpeg,a.ffprobe]:
  if not shutil.which(tool):raise ValueError('Missing '+tool)
 if os.path.lexists(a.report):raise FileExistsError(a.report)
 if a.out and a.out.resolve()==a.report.resolve():raise ValueError('Output and report must be distinct new paths')
 if not .1<=a.window_seconds<=10 or not 0<a.max_lag<=1 or not 0<a.min_correlation<=1:raise ValueError('Invalid bounded window settings')
 for x in[a.preview,a.reference]:
  if not x.is_file():raise ValueError('Input missing: '+str(x))
 if a.preview.resolve()==a.reference.resolve():raise ValueError('Inputs must be distinct')
 before={str(x.resolve()):(x.stat().st_size,x.stat().st_mtime_ns,x.stat().st_ino) for x in[a.preview,a.reference]}
 windows=json.loads(a.windows.read_text()) if a.windows else choose_windows(a.reference,a.window_count,a.max_lag,a.window_seconds)
 result=None;temp=None
 try:
  if a.mode=='verify':
   if a.out:raise ValueError('--out only applies to replace')
   result=verify(a.preview,a.reference,a,windows)
  else:
   if not a.out or a.out.suffix.lower()!='.mp4':raise ValueError('New --out MP4 required')
   if os.path.lexists(a.out):raise FileExistsError(a.out)
   meta=metadata_checks(a.preview,a.reference,a.ffprobe)
   if not meta['origin_check']['pass_zero_origin'] or not meta['duration_check']['pass_picture']:raise ValueError('Export matching native picture/PCM range with zero origin first')
   scale=movie_timescale(streams(meta['preview_probe'],'video')[0]['time_base'])
   h,tempname=tempfile.mkstemp(prefix='aac-staged-',suffix='.mp4',dir=a.out.resolve().parent);os.close(h);temp=Path(tempname);temp.unlink()
   cmd=[a.ffmpeg,'-nostdin','-v','error','-n','-i',str(a.preview),'-i',str(a.reference),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-profile:a','aac_low','-b:a','320k','-ar',str(RATE),'-movie_timescale',str(scale),'-movflags','+faststart',str(temp)]
   # No shortest/-t/offset: every native PCM sample and every original video packet is retained.
   capture(cmd);result=verify(temp,a.reference,a,windows);result['movie_timescale']=scale;result['remux_command']=cmd;result['original_preview']=str(a.preview.resolve());result['preview']=str(a.out.resolve());result['output_published']=False
   if result['status']=='PASS_ZERO_LAG':
    hashes=[video_hash(x,a.ffmpeg) for x in[a.preview,temp]]
    srcvideo=streams(probe(a.preview,a.ffprobe),'video')[0];newvideo=streams(probe(temp,a.ffprobe),'video')[0]
    attrs=['codec_name','profile','width','height','pix_fmt','color_range','color_space','color_transfer','color_primaries','field_order','r_frame_rate','avg_frame_rate','nb_frames']
    mismatches={k:[srcvideo.get(k),newvideo.get(k)] for k in attrs if srcvideo.get(k)!=newvideo.get(k)}
    exact=duration(srcvideo)==duration(newvideo) and origin(srcvideo)==origin(newvideo)
    result['picture_copy_check']=dict(source_payload_sha256=hashes[0],staged_payload_sha256=hashes[1],payload_identical=hashes[0]==hashes[1],exact_duration_and_origin_equal=exact,metadata_mismatches=mismatches)
    if hashes[0]!=hashes[1] or not exact or mismatches:result['status']='FAIL';result['failures'].append('PICTURE_COPY_MISMATCH')
    else:
     # Check inputs immediately before publication; never publish from a growing export.
     now={str(x.resolve()):(x.stat().st_size,x.stat().st_mtime_ns,x.stat().st_ino) for x in[a.preview,a.reference]}
     if now!=before:raise RuntimeError('Input changed before publication')
     # Hard-link publication is atomic and refuses an existing destination, including a race.
     os.link(temp,a.out);result['output_published']=True
  after={str(x.resolve()):(x.stat().st_size,x.stat().st_mtime_ns,x.stat().st_ino) for x in[a.preview,a.reference]};result['input_stats_unchanged']=before==after
  if before!=after:raise RuntimeError('Input changed during QA')
  result['selected_windows_seconds']=windows;result['window_selection']='Explicit' if a.windows else'Automatic bounded activity selection';result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
  write_new(a.report,result);print(json.dumps({k:result.get(k) for k in ['status','failures','output_published','reference_samples','sequential_decoded_samples']},indent=2));return 0 if result['status']=='PASS_ZERO_LAG' else 2
 except BaseException as ex:
  if not os.path.lexists(a.report):write_new(a.report,dict(status='ERROR',error=str(ex),output_published=bool(result and result.get('output_published')),preview=str(a.preview.resolve()),reference=str(a.reference.resolve())))
  raise
 finally:
  if temp:temp.unlink(missing_ok=True)
if __name__=='__main__':sys.exit(main())
