from jenskipper import jobs

from .asserts import assert_xml_strings_equal


def test_extract_pipeline_conf(data_dir):
    conf = data_dir.join('job_config.xml').open().read()
    pipe_bits, conf = jobs.extract_pipeline_conf(conf)
    assert pipe_bits == (['stupeflix'], 'SUCCESS')
    assert_xml_strings_equal(conf, JOB_WITHOUT_PIPELINE)


def test_merge_pipeline_conf(data_dir):
    merged = jobs.merge_pipeline_conf(JOB_WITHOUT_PIPELINE, ['stupeflix'],
                                      'SUCCESS')
    conf = data_dir.join('job_config.xml').open().read()
    assert_xml_strings_equal(merged, conf)


JOB_WITHOUT_PIPELINE = '''<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description/>
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
</project>'''  # NOQA