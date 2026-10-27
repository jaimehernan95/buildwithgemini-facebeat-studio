from auditor import FaceBeatAuditor


def test_system_audit():
    """Executes the full FaceBeat system auditor to catch any internal server errors,
    missing static assets, template syntax issues, or agent configuration errors."""
    auditor = FaceBeatAuditor()
    auditor.audit_environment_and_binaries()
    auditor.audit_static_assets_and_templates()
    auditor.audit_template_rendering()
    auditor.audit_fastapi_endpoints()
    auditor.audit_antigravity_agents()

    assert len(auditor.failures) == 0, f"Auditor found {len(auditor.failures)} failures: {auditor.failures}"
