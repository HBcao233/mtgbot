import asyncio
import util


pipe_kwargs = dict(
  stdout=asyncio.subprocess.PIPE, 
  stdin=asyncio.subprocess.PIPE,
  stderr=asyncio.subprocess.PIPE
)


async def video2gif(document_id, event, mid):
  palette = util.getCache(str(document_id) + '_palette.png')
  command = [
    'ffmpeg', 
    '-i', util.getCache(document_id), 
    '-vf', 'palettegen', 
    palette, '-y'
  ]
  proc = await asyncio.create_subprocess_exec(*command, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False

  output = util.getCache(str(document_id) + '.gif')
  command = [
    'ffmpeg', 
    '-i', img,
    '-i', palette,
    '-filter_complex', 'paletteuse',
    output, '-y'
  ]
  proc = await asyncio.create_subprocess_exec(*command, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  return output
  
async def tgs2gif(document_id):
  json_output = util.getCache(str(document_id) + '.json')
  output = util.getCache(str(document_id) + '.gif') 
  proc = await asyncio.create_subprocess_exec('cat', img, '|', 'gzip', '-d', '>', json_output, **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  
  proc = await asyncio.create_subprocess_exec('lottie2gif', json_output, '512x512', '00ffffff', **pipe_kwargs)
  stdout, stderr = await proc.communicate()
  if proc.returncode != 0 and stderr: 
    logger.error(stderr.decode('utf8'))
    return False
  await asyncio.create_subprocess_exec('mv', json_output + '.gif', output, **pipe_kwargs).wait()
  return output