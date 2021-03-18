import mmap


f = open("")
mm = mmap.mmap(f.fileno(), 0)


