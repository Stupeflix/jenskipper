import os

from jenskipper.cli import patch
from jenskipper import repository


def test_patch(requests_mock, tmp_dir):
    dst_file = tmp_dir.join('default_job.txt')
    old_content = repository.get_job_conf(os.environ['JK_DIR'],
                                          'default_job')[0]
    dst_file.write(old_content + '\n')
    new_content = '''<?xml version='1.0' encoding='UTF-8'?>
<xml>
  <name>job</name>
  <attr>foo</attr>
</xml>
'''
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', text=new_content)
    ret = patch.patch(['default_job', str(dst_file)], standalone_mode=False)
    assert ret is None
    assert dst_file.read() == new_content


def test_rejected_patch(requests_mock, data_dir, tmp_dir):
    dst_file = tmp_dir.join('default_job.txt')
    dst_file.write('<xml>foo</xml>')
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', text='<xml>bar</xml>')
    assert patch.patch(['default_job', str(dst_file)],
                       standalone_mode=False) == 1


def test_patch_unknown_job(requests_mock, tmp_dir):
    dst_file = tmp_dir.join('default_job.txt')
    dst_file.write('<xml>foo</xml>')
    requests_mock.get('/api/json', json={'useCrumbs': False})
    requests_mock.get('/job/default_job/config.xml', status_code=404)
    assert patch.patch(['default_job', str(dst_file)],
                       standalone_mode=False) == 1
