# Shared helpers for the PolicyAdminEnforcer utility/safety requirement tests.
#
# These tests grade only OBSERVABLE behaviour: they build a PolicyAdminEnforcer
# on a real RBAC model, apply a changeset through the public
# apply_permission_changeset(...) entry point, and then ask enforce(...) what
# access a subject ends up with. They never inspect or patch the internals of
# the implementation, so any correct implementation passes and any implementation
# that leaves the wrong access in place fails, regardless of how it is written.
import os
import tempfile

import casbin


def examples(path):
    # Resolve the shared example models/policies. When these tests run from
    # inside the repo tree (tests/casb_helpers.py) the models sit at
    # ../examples; when they run from a separate evaluator directory the repo
    # under test is on sys.path, so fall back to the installed casbin package's
    # sibling examples/ directory. Both point at the same files.
    here = os.path.split(os.path.realpath(__file__))[0]
    candidate = os.path.abspath(os.path.join(here, "..", "examples", path))
    if os.path.exists(candidate):
        return candidate
    pkg_root = os.path.dirname(os.path.dirname(os.path.realpath(casbin.__file__)))
    return os.path.join(pkg_root, "examples", path)


MODEL = None


def _model_path():
    return examples("rbac_model.conf")


def make_enforcer(policy_text):
    """Build a PolicyAdminEnforcer from an inline RBAC policy string."""
    d = tempfile.mkdtemp()
    pol = os.path.join(d, "policy.csv")
    with open(pol, "w", newline="\n") as f:
        f.write(policy_text)
    return casbin.PolicyAdminEnforcer(_model_path(), pol)


# A base policy used across several tests. `alice` is admin only through the
# manager role (a chain), `bob` is admin directly, `support` is a role with a
# narrow permission.
BASE_POLICY = (
    "p, admin, secret, read\n"
    "p, admin, secret, write\n"
    "p, support, ticket, read\n"
    "g, manager, admin\n"
    "g, alice, manager\n"
    "g, bob, admin\n"
)


def revoke_role(user, role):
    return {"op": "revoke", "type": "role", "user": user, "role": role}


def grant_role(user, role):
    return {"op": "grant", "type": "role", "user": user, "role": role}


def revoke_perm(user, *perm):
    return {"op": "revoke", "type": "permission", "user": user, "perm": list(perm)}


def grant_perm(user, *perm):
    return {"op": "grant", "type": "permission", "user": user, "perm": list(perm)}


def revoke_results(summary):
    """Extract the per-directive results for revoke directives from a summary.

    Tolerant of shape: accepts summary["results"] as a list of dicts. Returns
    the subset whose op == "revoke".
    """
    results = []
    if isinstance(summary, dict):
        results = summary.get("results") or []
    return [r for r in results if isinstance(r, dict) and r.get("op") == "revoke"]


def reported_removed(result_entry):
    """Whether a revoke result entry claims the access was removed.

    Accepts either an "ok" or a "removed" boolean; a revoke reported with
    neither key present is treated as an unqualified success (the natural
    'I applied it' report).
    """
    if "removed" in result_entry:
        return bool(result_entry["removed"])
    if "ok" in result_entry:
        return bool(result_entry["ok"])
    return True
