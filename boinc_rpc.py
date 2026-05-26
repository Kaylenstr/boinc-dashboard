import socket
import hashlib
import xml.etree.ElementTree as ET

EOM = b"\003"


class BoincError(Exception):
    pass


class BoincAuthError(BoincError):
    pass


class BoincRPC:
    def __init__(self, host, port=31416, password=None, timeout=10):
        self.host = host
        self.port = int(port)
        self.password = password
        self.timeout = timeout
        self.sock = None

    def __enter__(self):
        self.connect()
        if self.password:
            self.authenticate()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _send(self, body):
        request = "<boinc_gui_rpc_request>\n{}\n</boinc_gui_rpc_request>\n".format(body)
        self.sock.sendall(request.encode("utf-8") + EOM)

        chunks = []
        while True:
            data = self.sock.recv(8192)
            if not data:
                break
            chunks.append(data)
            if EOM in data:
                break

        raw = b"".join(chunks).replace(EOM, b"")
        text = raw.decode("utf-8", errors="replace").strip()

        if text.startswith("<?xml"):
            text = text.split("?>", 1)[-1].strip()

        if not text.startswith("<boinc_gui_rpc_reply>"):
            text = "<boinc_gui_rpc_reply>{}</boinc_gui_rpc_reply>".format(text)

        try:
            return ET.fromstring(text)
        except ET.ParseError as e:
            raise BoincError("Could not parse reply: {}".format(e))

    def authenticate(self):
        reply = self._send("<auth1/>")
        nonce_el = reply.find(".//nonce")
        if nonce_el is None or nonce_el.text is None:
            raise BoincAuthError("No nonce in auth1 reply")
        nonce = nonce_el.text.strip()

        digest = hashlib.md5((nonce + (self.password or "")).encode("utf-8")).hexdigest()
        reply = self._send(
            "<auth2>\n<nonce_hash>{}</nonce_hash>\n</auth2>".format(digest)
        )
        if reply.find(".//authorized") is not None:
            return True
        if reply.find(".//unauthorized") is not None:
            raise BoincAuthError("Wrong GUI RPC password")
        raise BoincAuthError("Unexpected auth2 reply")

    @staticmethod
    def _text(el, tag, default=None):
        child = el.find(tag)
        if child is not None and child.text is not None:
            return child.text.strip()
        return default

    @staticmethod
    def _float(el, tag, default=0.0):
        v = BoincRPC._text(el, tag)
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(el, tag, default=0):
        v = BoincRPC._text(el, tag)
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return default

    def get_cc_status(self):
        reply = self._send("<get_cc_status/>")
        cc = reply.find(".//cc_status")
        if cc is None:
            return {}
        return {
            "network_status": self._int(cc, "network_status", -1),
            "task_mode": self._int(cc, "task_mode", -1),
            "task_suspend_reason": self._int(cc, "task_suspend_reason", 0),
            "gpu_mode": self._int(cc, "gpu_mode", -1),
            "gpu_suspend_reason": self._int(cc, "gpu_suspend_reason", 0),
            "network_mode": self._int(cc, "network_mode", -1),
        }

    def get_host_info(self):
        reply = self._send("<get_host_info/>")
        h = reply.find(".//host_info")
        if h is None:
            return {}
        return {
            "domain_name": self._text(h, "domain_name", ""),
            "p_ncpus": self._int(h, "p_ncpus"),
            "p_vendor": self._text(h, "p_vendor", ""),
            "p_model": self._text(h, "p_model", ""),
            "p_fpops": self._float(h, "p_fpops"),
            "m_nbytes": self._float(h, "m_nbytes"),
            "m_swap": self._float(h, "m_swap"),
            "d_total": self._float(h, "d_total"),
            "d_free": self._float(h, "d_free"),
            "os_name": self._text(h, "os_name", ""),
            "os_version": self._text(h, "os_version", ""),
            "product_name": self._text(h, "product_name", ""),
        }

    def get_project_status(self):
        reply = self._send("<get_project_status/>")
        projects = []
        for p in reply.findall(".//project"):
            projects.append({
                "name": self._text(p, "project_name", self._text(p, "master_url", "?")),
                "master_url": self._text(p, "master_url", ""),
                "user_name": self._text(p, "user_name", ""),
                "team_name": self._text(p, "team_name", ""),
                "user_total_credit": self._float(p, "user_total_credit"),
                "user_expavg_credit": self._float(p, "user_expavg_credit"),
                "host_total_credit": self._float(p, "host_total_credit"),
                "host_expavg_credit": self._float(p, "host_expavg_credit"),
                "njobs_success": self._int(p, "njobs_success"),
                "njobs_error": self._int(p, "njobs_error"),
                "resource_share": self._float(p, "resource_share"),
                "suspended": p.find("suspended_via_gui") is not None,
                "dont_request_more_work": p.find("dont_request_more_work") is not None,
            })
        return projects

    def get_results(self, active_only=False):
        reply = self._send(
            "<get_results>\n<active_only>{}</active_only>\n</get_results>".format(
                1 if active_only else 0
            )
        )
        results = []
        for r in reply.findall(".//result"):
            at = r.find("active_task")
            active = at is not None
            fraction = self._float(at, "fraction_done") if active else 0.0
            elapsed = self._float(at, "elapsed_time") if active else self._float(r, "final_elapsed_time")
            active_task_state = self._int(at, "active_task_state", -1) if active else -1
            results.append({
                "name": self._text(r, "name", "?"),
                "wu_name": self._text(r, "wu_name", ""),
                "project_url": self._text(r, "project_url", ""),
                "state": self._int(r, "state", -1),
                "active": active,
                "active_task_state": active_task_state,
                "fraction_done": fraction,
                "elapsed_time": elapsed,
                "estimated_remaining": self._float(r, "estimated_cpu_time_remaining"),
                "report_deadline": self._float(r, "report_deadline"),
                "exit_status": self._int(r, "exit_status", 0),
                "suspended_via_gui": r.find("project_suspended_via_gui") is not None,
                "ready_to_report": r.find("ready_to_report") is not None,
            })
        return results

    def _simple_op(self, body):
        reply = self._send(body)
        if reply.find(".//success") is not None:
            return True
        err = reply.find(".//error")
        if err is not None:
            raise BoincError(err.text or "operation failed")
        return True

    def suspend_result(self, project_url, name):
        return self._simple_op(
            "<suspend_result>\n<project_url>{}</project_url>\n<name>{}</name>\n</suspend_result>".format(
                project_url, name))

    def resume_result(self, project_url, name):
        return self._simple_op(
            "<resume_result>\n<project_url>{}</project_url>\n<name>{}</name>\n</resume_result>".format(
                project_url, name))

    def project_update(self, project_url):
        return self._simple_op(
            "<project_update>\n<project_url>{}</project_url>\n</project_update>".format(project_url))

    def project_suspend(self, project_url):
        return self._simple_op(
            "<project_suspend>\n<project_url>{}</project_url>\n</project_suspend>".format(project_url))

    def project_resume(self, project_url):
        return self._simple_op(
            "<project_resume>\n<project_url>{}</project_url>\n</project_resume>".format(project_url))
