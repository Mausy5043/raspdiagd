#!/usr/bin/python

# source: http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail

class FileExtremities(file):
  """
  A python module to retrieve the first or last `n` lines of a file.

  Usage:

  f = FileExtremities('path/to/file', 'r')
  f.head(3)
  f.tail(3)
  """
  def head(self, lines_2find=1):
    self.seek(0)                            #Rewind file
    return [self.next() for x in xrange(lines_2find)]

  def tail(self, lines_2find=1):
    self.seek(0, 2)                         #go to end of file
    bytes_in_file = self.tell()
    lines_found, total_bytes_scanned = 0, 0
    while (lines_2find+1 > lines_found and bytes_in_file > total_bytes_scanned):
      byte_block = min(1024, bytes_in_file-total_bytes_scanned)
      self.seek(-(byte_block+total_bytes_scanned), 2)
      total_bytes_scanned += byte_block
      lines_found += self.read(1024).count('\n')
    self.seek(-total_bytes_scanned, 2)
    line_list = list(self.readlines())
    return line_list[-lines_2find:]
