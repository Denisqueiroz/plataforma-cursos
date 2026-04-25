import os
import re
import mimetypes
from django.http import StreamingHttpResponse, HttpResponse, Http404

def range_re(range_header):
    match = re.match(r'bytes=(\d+)-(\d*)', range_header)
    if match:
        start, end = match.groups()
        start = int(start) if start else 0
        end = int(end) if end else None
        return start, end
    return None, None

def ranged_serve(request, path, document_root=None, show_indexes=False):
    fullpath = os.path.join(document_root, path)
    if not os.path.exists(fullpath):
        raise Http404(f"O arquivo {path} não foi encontrado.")

    range_header = request.META.get('HTTP_RANGE', '').strip()
    size = os.path.getsize(fullpath)
    content_type, encoding = mimetypes.guess_type(fullpath)
    content_type = content_type or 'application/octet-stream'

    if range_header:
        start, end = range_re(range_header)
        if start is None:
            return HttpResponse(status=400)
        
        if end is None:
            end = size - 1
            
        if start >= size:
            return HttpResponse(status=416) # Range Not Satisfiable
            
        length = end - start + 1

        def file_iterator(file_path, offset=0, bytes_to_read=None):
            with open(file_path, 'rb') as f:
                f.seek(offset)
                if bytes_to_read:
                    bytes_remaining = bytes_to_read
                    while bytes_remaining > 0:
                        chunk_size = min(8192, bytes_remaining)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        bytes_remaining -= len(data)
                        yield data
                else:
                    while True:
                        data = f.read(8192)
                        if not data:
                            break
                        yield data

        response = StreamingHttpResponse(file_iterator(fullpath, start, length), status=206, content_type=content_type)
        response['Content-Length'] = str(length)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Accept-Ranges'] = 'bytes'
        return response

    else:
        def file_iterator(file_path):
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    yield data
                    
        response = StreamingHttpResponse(file_iterator(fullpath), content_type=content_type)
        response['Content-Length'] = str(size)
        response['Accept-Ranges'] = 'bytes'
        return response
