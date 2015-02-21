import datetime
import re
from .utils import trace

from pkg_resources import parse_version, SetuptoolsVersion, iter_entry_points


def callable_or_entrypoint(group, callable_or_name):
    trace('ep', (group, callable_or_name))
    if isinstance(callable_or_name, str):
        ep = next(iter_entry_points(group, callable_or_name))
        return ep.load()
    else:
        return callable_or_name


def tag_to_version(tag):
    trace('tag', tag)
    version = tag.rsplit('-', 1)[-1]
    version = parse_version(version)
    trace('version', repr(version))
    if isinstance(version, SetuptoolsVersion):
        return version


def tags_to_versions(tags):
    versions = map(tag_to_version, tags)
    return [v for v in versions if v is not None]


class ScmVersion(object):
    def __init__(self, tag_version,
                 distance=None, node=None, dirty=False,
                 **kw):
        self.tag = tag_version
        if dirty and distance is None:
            distance = 0
        self.distance = distance
        self.node = node
        self.time = datetime.datetime.now()
        self.extra = kw
        self.dirty = dirty

    @property
    def exact(self):
        return self.distance is None

    def __repr__(self):
        return self.format_with(
            '<ScmVersion {tag} d={distance}'
            ' n={node} d={dirty} x={extra}>')

    def format_with(self, fmt):
        return fmt.format(
            time=self.time,
            tag=self.tag, distance=self.distance,
            node=self.node, dirty=self.dirty, extra=self.extra)


def meta(tag, distance=None, dirty=False, node=None, **kw):
    if isinstance(tag, str):
        tag = tag_to_version(tag)
    trace('version', tag)

    assert tag is not None, 'cant parse version %s' % tag
    return ScmVersion(tag, distance, node, dirty, **kw)


def guess_next_version(tag_version, distance):
    version = str(tag_version)
    if '.dev' in version:
        prefix, tail = version.rsplit('.dev', 1)
        assert tail == '0', 'own dev numbers are unsupported'
        return '%s.dev%s' % (prefix, distance)
    else:
        prefix, tail = re.match('(.*?)(\d+)$', version).groups()
        return '%s%d.dev%s' % (prefix, int(tail) + 1, distance)


def guess_next_dev_version(version):
    if version.exact:
        return version.format_with('{tag}')
    else:
        return guess_next_version(version.tag, version.distance)


def get_local_node_and_date(version):
    if version.exact:
        if version.dirty:
            return version.format_with("+d{time:%Y%m%d}")
        else:
            return ''
    else:
        if version.dirty:
            return version.format_with("+n{node}.d{time:%Y%m%d}")
        else:
            return version.format_with("+n{node}")


def get_local_dirty_tag(version):
    if version.dirty:
        return '+dirty'
    else:
        return ''


def postrelease_version(version):
    if version.exact:
        return version.format_with('{tag}')
    else:
        return version.format_with('{tag}.post{distance}')


def format_version(version, **config):
    trace('scm version', version)
    trace('config', config)
    version_scheme = callable_or_entrypoint(
        'setuptools_scm.version_scheme', config['version_scheme'])
    local_scheme = callable_or_entrypoint(
        'setuptools_scm.local_scheme', config['local_scheme'])
    main_version = version_scheme(version)
    trace('version', main_version)
    local_version = local_scheme(version)
    trace('local_version', local_version)
    return version_scheme(version) + local_scheme(version)