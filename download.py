import socket
import sys
import threading
import urllib2


socket.setdefaulttimeout(120)   # 2 minutes
urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor()))


threads = []
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5)'
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71'
    'Safari/537.36',

    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',

    'Accept': 'text/xml,application/xml,application/xhtml+xml,'
    'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
}


def get_range_list(file_size, split_num):
    start = 0
    block_size = file_size / split_num
    range_list = []
    for i in range(split_num):
        if i == 0:
            range_list.append('%s-%s' % (start, start+block_size))
        else:
            range_list.append('%s-%s' % (start+1, (start+block_size)))
        start += block_size
    return range_list


def get_file_size_and_extension(url):
    try:
        data = urllib2.urlopen(url)
        file_size = int(data.info()['Content-Length'])
        if not file_size:
            print "Content-Length not available! Please try another link!"
            sys.exit(1)
        extension = data.info()['Content-Type'].split('/')[1]
        return file_size, extension

    except:
        print "Connection Error!"
        sys.exit(1)


class fetch_data(threading.Thread):
    def __init__(self, url, file_name, range):
        threading.Thread.__init__(self)
        self.url = url
        self.file_name = file_name
        self.range = range
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        global total_downloaded_data
        request = urllib2.Request(self.url, None, headers)
        request.add_header('Range', 'bytes=%s' % (self.range))

        try:
            data = urllib2.urlopen(request).read()
        except:
            print "Connection Error!"
            sys.exit(1)

        self.data = data


def main():
    try:
        url = sys.argv[1]
        file_name = sys.argv[2]
        file_size, extension = get_file_size_and_extension(url)
        range_list = get_range_list(file_size, 5)

        for i in range(5):
            # spawn a thread in each iteration
            current_thread = fetch_data(url, file_name, range_list[i])
            current_thread.start()
            threads.append(current_thread)

        for t in threads:
            t.join()

        with open(file_name+"."+extension, 'w') as fh:
            for t in threads:
                fh.write(t.data)
        print "Done!"

    except KeyboardInterrupt:
        print 'Shutting down threads.'
        for thread in threads:
            thread.stop()
        sys.exit(1)

    except Exception, e:
        print e
        print 'Shutting down threads.'
        for thread in threads:
            thread.stop()
        pass


if __name__ == "__main__":
    main()
