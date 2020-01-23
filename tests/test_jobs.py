# -*- coding: utf8 -*-

from xml.etree import ElementTree

from jenskipper import jobs

from .asserts import assert_xml_strings_equal


def test_extract_pipeline_conf(data_dir):
    conf = data_dir.join('job_config.xml').read_text('utf8')
    pipe_bits, conf = jobs.extract_pipeline_conf(conf)
    assert pipe_bits == (['stupeflix'], 'SUCCESS')
    assert_xml_strings_equal(conf, JOB_WITHOUT_PIPELINE)


def test_merge_pipeline_conf(data_dir):
    merged = jobs.merge_pipeline_conf(JOB_WITHOUT_PIPELINE, ['stupeflix'],
                                      'SUCCESS')
    conf = data_dir.join('job_config.xml').read_text('utf8')
    assert_xml_strings_equal(merged, conf)


def test_get_conf_hash(data_dir):
    conf = data_dir.join('job_config.xml').read_text('utf8')
    assert jobs.get_conf_hash(conf) == \
        '755f757faa53968a68a7b13851ce8052c7dfee97'


def test_append_hash_in_description(data_dir):
    conf = data_dir.join('job_config.xml').read_text('utf8')
    rendered_conf = jobs.append_hash_in_description(conf)
    tree = ElementTree.fromstring(rendered_conf)
    elt = tree.find('.//description')
    mark = '-*- jenskipper-hash: 755f757faa53968a68a7b13851ce8052c7dfee97 -*-'
    assert elt.text.endswith(mark)


def test_extract_hash_from_description(data_dir):
    conf = data_dir.join('job_config.xml').read_text('utf8')
    with_hash = jobs.append_hash_in_description(conf)
    conf_hash, without_hash = jobs.extract_hash_from_description(with_hash)
    assert conf_hash == '755f757faa53968a68a7b13851ce8052c7dfee97'
    assert_xml_strings_equal(without_hash, conf)


def test_extract_hash_from_description_without_hash(data_dir):
    conf = data_dir.join('job_config.xml').read_text('utf8')
    conf_hash, unchanged_conf = jobs.extract_hash_from_description(conf)
    assert conf_hash is None
    assert_xml_strings_equal(unchanged_conf, conf)


def test_extract_hash_from_text():
    f = jobs.extract_hash_from_text
    h = '-*- jenskipper-hash: fff -*-'
    assert f('foo') == (None, 'foo')
    assert f(h) == ('fff', '')
    assert f('foo\n\n%s' % h) == ('fff', 'foo')
    assert f('foo\r\n\r\n%s' % h) == ('fff', 'foo')
    assert f('foo%s' % h) == ('fff', 'foo')


def test_remove_disabled_flag():
    xml = '<project><disabled>false</disabled></project>'
    assert jobs.remove_disabled_flag(xml) == '<project />'


def test_transfuse_disabled_flag_replace():
    from_xml = '<project><disabled>false</disabled></project>'
    to_xml = '<project><disabled>true</disabled></project>'
    assert jobs.transfuse_disabled_flag(from_xml, to_xml) == from_xml


def test_transfuse_disabled_flag_add():
    from_xml = '<project><disabled>false</disabled></project>'
    to_xml = '<project></project>'
    assert jobs.transfuse_disabled_flag(from_xml, to_xml) == from_xml


def test_transfuse_disabled_flag_noop():
    from_xml = '<project></project>'
    to_xml = '<project><disabled>true</disabled></project>'
    assert jobs.transfuse_disabled_flag(from_xml, to_xml) == to_xml


JOB_WITHOUT_PIPELINE = """<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>€</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <jenkins.plugins.slack.SlackNotifier_-SlackJobProperty plugin="slack@1.8">
      <teamDomain/>
      <token/>
      <room/>
      <startNotification>false</startNotification>
      <notifySuccess>false</notifySuccess>
      <notifyAborted>false</notifyAborted>
      <notifyNotBuilt>false</notifyNotBuilt>
      <notifyUnstable>false</notifyUnstable>
      <notifyFailure>false</notifyFailure>
      <notifyBackToNormal>false</notifyBackToNormal>
      <notifyRepeatedFailure>false</notifyRepeatedFailure>
      <includeTestSummary>false</includeTestSummary>
      <showCommitList>false</showCommitList>
      <includeCustomMessage>false</includeCustomMessage>
      <customMessage/>
    </jenkins.plugins.slack.SlackNotifier_-SlackJobProperty>
    <hudson.plugins.throttleconcurrents.ThrottleJobProperty plugin="throttle-concurrents@1.8.4">
      <maxConcurrentPerNode>0</maxConcurrentPerNode>
      <maxConcurrentTotal>0</maxConcurrentTotal>
      <throttleEnabled>false</throttleEnabled>
      <throttleOption>project</throttleOption>
    </hudson.plugins.throttleconcurrents.ThrottleJobProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
    </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>"""  # NOQA
