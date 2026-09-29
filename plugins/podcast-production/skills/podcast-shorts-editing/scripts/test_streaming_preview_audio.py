#!/usr/bin/env python3
"""In-memory boundary/index checks; native codec validation is a separate pilot."""
import contextlib,io,json,shutil,subprocess,sys,tempfile,unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
import numpy as np
import streaming_preview_audio as m
class Chunked(io.BytesIO):
 def read(self,n=-1):return super().read(min(n,17))
class FakeProc:
 def __init__(self,data):self.stdout=Chunked(data)
 def wait(self):return 0
 def kill(self):pass
class Tests(unittest.TestCase):
 def test_positive_lag_sign(self):
  a=np.random.default_rng(6).normal(size=5000);b=np.zeros(5400);b[200+37:200+37+5000]=a
  q=m.correlation(a,b,200);self.assertEqual(q['lag_samples'],37);self.assertGreater(q['correlation'],.999999)
 def test_negative_lag_sign(self):
  a=np.random.default_rng(8).normal(size=5000);b=np.zeros(5400);b[200-27:200-27+5000]=a
  self.assertEqual(m.correlation(a,b,200)['lag_samples'],-27)
 def test_streaming_capture_tail_and_partial_byte_reads(self):
  x=np.arange(400,dtype='float32').reshape(200,2)/500
  with patch.object(m.subprocess,'Popen',return_value=FakeProc(x.astype('<f4').tobytes())):
   d=m.sequential_decode('not-read',[(0,20),(51,70),(190,200),(198,205)],8,'not-run')
  self.assertEqual(d['samples'],200);self.assertEqual(d['filled'],[20,19,10,2]);np.testing.assert_equal(d['buffers'][1],x[51:70]);np.testing.assert_equal(d['tail'],x[-8:])
 def test_reject_out_of_distribution(self):
  with self.assertRaises(ValueError):m.validate_windows([[1,2]]*6,48000*12,6,.15)
 def test_reject_unbounded_windows(self):
  with self.assertRaises(ValueError):m.validate_windows([[2,20]]*6,48000*180,6,.15)
 def test_tail_missing_signal_fails_numeric_criteria(self):
  x=np.random.default_rng(2).normal(0,.1,4096);q=m.aligned_metric(x,np.zeros_like(x));self.assertIsNone(q['zero_lag_correlation']);self.assertEqual(q['candidate_rms_dbfs'],-240)
 def test_movie_clock_represents_video_and_audio_ticks(self):
  for timebase,expected in [('1/30000',240000),('1/90000',720000),('1/25',48000)]:
   scale=m.movie_timescale(timebase);self.assertEqual(scale,expected)
   self.assertEqual((Fraction(timebase)*scale).denominator,1)
   self.assertEqual((Fraction(1,48000)*scale).denominator,1)
  with self.assertRaisesRegex(ValueError,'integer range'):m.movie_timescale('1/2147483647')
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg codec regression needs ffmpeg and ffprobe')
 def test_fractional_millisecond_duration_survives_aac_replacement(self):
  # 241 NTSC frames end between movie milliseconds. A 1000Hz movie clock
  # loses about 18 audio samples; exact clocks must retain the 2-sample test.
  if 'libx264' not in m.capture(['ffmpeg','-v','error','-encoders']).decode():self.skipTest('Codec fixture requires libx264; the production helper does not')
  with tempfile.TemporaryDirectory() as folder:
   base=Path(folder);pcm=base/'reference.wav';video=base/'picture.mp4';native=base/'native.mp4';out=base/'corrected.mp4';report=base/'qa.json'
   frames=round(Fraction(241*1001*48000,30000))
   noise=np.random.default_rng(17).normal(size=frames+64)
   kernel=np.hanning(65);kernel/=kernel.sum()
   x=np.convolve(noise,kernel,mode='valid')*.25
   m.sf.write(pcm,np.column_stack([x,x*.93]),48000,subtype='PCM_24')
   m.capture(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=c=black:s=64x64:r=30000/1001','-frames:v','241','-c:v','libx264','-pix_fmt','yuv420p',str(video)])
   m.capture(['ffmpeg','-nostdin','-v','error','-i',str(video),'-i',str(pcm),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k',str(native)])
   before=m.metadata_checks(native,pcm,'ffprobe')
   self.assertFalse(before['duration_check']['pass_audio'])
   argv=['streaming_preview_audio.py','replace','--preview',str(native),'--reference',str(pcm),'--out',str(out),'--report',str(report),'--window-count','6']
   with patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
    self.assertEqual(m.main(),0)
   q=json.loads(report.read_text())
   self.assertTrue(q['output_published']);self.assertTrue(q['picture_copy_check']['payload_identical'])
   self.assertEqual(q['movie_timescale'],240000)
   self.assertEqual(q['duration_check']['audio_minus_reference_samples'],0)
   self.assertEqual(q['duration_check']['tolerance_samples'],2)
   self.assertTrue(q['duration_check']['pass_picture']);self.assertTrue(q['duration_check']['pass_audio'])
if __name__=='__main__':unittest.main()
