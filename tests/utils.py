def serve_file(httpserver, path, code=200):
    with open(str(path), 'rb') as fp:
        content = fp.read()
    httpserver.serve_content(content,
                             code=code,
                             headers={'content-type': 'text/html; charset=UTF-8'})
    return content.decode('utf8')
