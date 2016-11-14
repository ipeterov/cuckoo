# Copyright (C) 2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import responses
import tempfile

from cuckoo.core.plugins import RunReporting
from cuckoo.common.config import Config
from cuckoo.common.files import Folders, Files
from cuckoo.misc import set_cwd, cwd
from cuckoo.reporting.jsondump import JsonDump

def task(task_id, options, conf, results):
    Folders.create(cwd(), ["conf", "storage"])
    Folders.create(cwd("storage"), ["analyses", "binaries"])
    Folders.create(cwd("storage", "analyses"), "%s" % task_id)
    Folders.create(cwd("storage", "analyses", "%s" % task_id), [
        "reports"
    ])

    defaults = Config(
        "reporting", strict=True,
        cfg=cwd("cwd", "conf", "reporting.conf", private=True)
    )

    reporting_conf = []
    for section, values in defaults.sections.items():
        reporting_conf.append("[%s]" % section)
        for key, value in values.items():
            raw = conf.get(section, values).get(key, value)
            reporting_conf.append("%s = %s" % (key, {
                True: "yes", False: "no", None: "",
            }.get(raw, raw)))

    Files.create(cwd("conf"), "reporting.conf", "\n".join(reporting_conf))

    task = {
        "id": task_id,
        "options": options,
    }
    RunReporting(task, results).run()

@responses.activate
def test_empty():
    set_cwd(tempfile.mkdtemp())

    conf = {
        "jsondump": {
            "enabled": True,
        },
    }
    report_path = cwd("storage", "analyses", "1", "reports", "report.json")

    task(1, {}, conf, {})
    assert open(report_path, "rb").read() == "{}"

    conf = {
        "mattermost": {
            "enabled": True,
            "url": "http://localhost/matter",
        },
    }
    responses.add(responses.POST, "http://localhost/matter")
    task(2, {}, conf, {})
    assert len(responses.calls) == 1

    # TODO Somehow catch the exception.
    conf["mattermost"]["url"] = "http://localhost/matter2"
    responses.add(responses.POST, "http://localhost/matter2", status=403)
    task(2, {}, conf, {})
    assert len(responses.calls) == 2
