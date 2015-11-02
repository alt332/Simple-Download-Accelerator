#!/usr/bin/python
import os
import socket
import sys
import threading
import time
import urllib2


socket.setdefaulttimeout(120)   # 2 mins
urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor()))


threads = []
total_download = 0.0
retry_count = 10
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5)'
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71'
    'Safari/537.36',

    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',

    'Accept': 'text/xml,application/xml,application/xhtml+xml,'
    'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
}


def get_lengths_and_offsets(file_size, split_num):
    block_size = int(file_size) / split_num
    lengths = [block_size for i in range(split_num)]
    lengths[0] += int(file_size) % split_num
    offsets = []
    start = 0
    for i in range(len(lengths)):
        if i == 0:
            offsets.append(start)
        else:
            offsets.append(start+1)
        start += lengths[i]
    return lengths, offsets


def get_file_size_and_extension(url):
    try:
        data = urllib2.urlopen(url)
        file_size = int(data.info()['Content-Length']) + 0.0
        if not file_size:
            print "Content-Length not available! Please try another link!"
            sys.exit(1)
        extension = data.info()['Content-Type'].split('/')[1]
        return file_size, extension

    except:
        print "\n Connection Error!"
        sys.exit(1)


class fetch_data(threading.Thread):
    def __init__(self, url, file_name, length, start_offset):
        threading.Thread.__init__(self)
        self.name = threading.current_thread().name
        self.url = url
        self.file_name = file_name
        self.length = length
        self.stop_thread = False
        self.start_offset = start_offset

    def run(self):
        global total_download, retry_count
        request = urllib2.Request(self.url, None, headers)

        if self.length == 0 or retry_count == 0 or self.stop_thread:
            return
        request.add_header('Range', 'bytes=%s-%s' % (self.start_offset,
                                                     self.start_offset +
                                                     self.length))

        while True:
            if self.stop_thread:
                sys.exit(1)
            try:
                data = urllib2.urlopen(request)
            except urllib2.URLError:
                retry_count -= 1
                if retry_count == 0:
                    self.stop_thread = True
                return
            else:
                break

        output = os.open(self.file_name+".part", os.O_WRONLY)
        os.lseek(output, self.start_offset, os.SEEK_SET)

        block_size = 1024

        while self.length > 0:
            if self.stop_thread:
                return
            if self.length >= block_size:
                fetch_size = block_size
            else:
                fetch_size = self.length
            try:
                data_block = data.read(fetch_size)

                if len(data_block) != fetch_size \
                   and (fetch_size - len(data_block)) > 1:
                    self.run()
                    return

                self.length -= fetch_size
                sys.stdout.flush()
                os.write(output, data_block)
                self.start_offset += len(data_block)
                total_download += len(data_block)
            except socket.timeout:
                self.run()
                pass


def main():
    try:
        url = sys.argv[1]
        file_name = sys.argv[2]
        file_size, extension = get_file_size_and_extension(url)
        lengths, offsets = get_lengths_and_offsets(file_size, 10)

        os.open(file_name+".part", os.O_CREAT | os.O_WRONLY)

        for i in range(10):
            # spawn a thread in each iteration
            current_thread = fetch_data(url, file_name, lengths[i], offsets[i])
            current_thread.start()
            threads.append(current_thread)

        while threading.active_count() > 1:
            sys.stdout.flush()
            percent = (total_download/file_size) * 100.0
            sys.stdout.write('\r %.2f%%' % percent)
            time.sleep(1)

        if retry_count == 0:
            os.remove(file_name+'.part')
            print '\n Connection Error!'
        else:
            os.rename(file_name+".part", file_name+"."+extension)
            sys.stdout.write('\r %.2f%%' % 100.00)
            print '\n Done!'
        sys.exit(1)

    except KeyboardInterrupt:
        for thread in threads:
            thread.stop_thread = True
        sys.exit(1)

    except Exception, e:
        print e
        for thread in threads:
            thread.stop_thread = True
        sys.exit(1)


if __name__ == "__main__":
    main()
