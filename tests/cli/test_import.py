from jenskipper.cli import import_


def test_import(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'jobs': [{'name': 'new_job'}],
                                         'useCrumbs': False})
    job_xml = '<xml>foo</xml>'
    requests_mock.get('/job/new_job/config.xml', text=job_xml)
    repos_dir = tmp_dir.join('repos')
    ret = import_.import_(['http://test.jenskipper.com', str(repos_dir)],
                          standalone_mode=False)
    assert ret is None
    assert repos_dir.join('templates', 'new_job.xml').read() == job_xml


def test_import_repos_dir_exists(requests_mock, tmp_dir):
    requests_mock.get('/api/json', json={'useCrumbs': False})
    repos_dir = tmp_dir.join('repos')
    repos_dir.ensure(dir=True)
    exit_code = import_.import_(['http://test.jenskipper.com', str(repos_dir)],
                                standalone_mode=False)
    assert exit_code == 1
