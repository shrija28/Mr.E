import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

const AdminInstitutions = () => {
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [pendingAction, setPendingAction] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchInstitutions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/api/admin/institutions';
      if (filterStatus) {
        url += `?subscription_status=${encodeURIComponent(filterStatus)}`;
      }
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) {
        let msg = `Server error: ${res.status}`;
        if (res.status === 401) msg = 'Session expired. Please log in again.';
        if (res.status === 403) msg = 'Access denied: Platform Admin privileges required.';
        throw new Error(msg);
      }
      const data = await res.json();
      setInstitutions(data.institutions || []);
    } catch (err) {
      console.error('Failed to load institutions:', err);
      setError(err.message || 'Network error occurred while fetching institutions.');
    } finally {
      setLoading(false);
    }
  }, [filterStatus]);

  useEffect(() => {
    fetchInstitutions();
  }, [fetchInstitutions]);

  const handleActionConfirm = async () => {
    if (!pendingAction) return;
    const { action, instId } = pendingAction;
    setActionLoading(true);
    try {
      const url = `/api/admin/institutions/${instId}/${action}`;
      const res = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        alert((errData && errData.detail) || `Failed to ${action} institution.`);
        return;
      }
      setPendingAction(null);
      await fetchInstitutions();
    } catch (err) {
      console.error(`Failed to ${action} institution:`, err);
      alert('Network error occurred.');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const s = (status || 'none').toLowerCase();
    const styleMap = {
      active: { background: 'rgba(5, 150, 105, 0.15)', color: 'var(--green-l, #10b981)' },
      trial: { background: 'rgba(5, 150, 105, 0.1)', color: 'var(--green-l, #10b981)' },
      inactive: { background: 'rgba(107, 114, 128, 0.15)', color: 'var(--muted, #94a3b8)' },
      overdue: { background: 'rgba(217, 119, 6, 0.15)', color: 'var(--yellow-l, #f59e0b)' },
      grace_period: { background: 'rgba(217, 119, 6, 0.12)', color: 'var(--yellow-l, #f59e0b)' },
      expired: { background: 'rgba(220, 38, 38, 0.12)', color: 'var(--red-l, #ef4444)' },
      none: { background: 'rgba(107, 114, 128, 0.1)', color: 'var(--muted2, #64748b)' },
    };
    const currentStyle = styleMap[s] || styleMap.none;

    return (
      <span
        style={{
          ...currentStyle,
          padding: '3px 9px',
          borderRadius: '8px',
          fontSize: '0.72rem',
          fontWeight: '700',
          display: 'inline-block',
          letterSpacing: '0.02em',
          textTransform: 'capitalize',
        }}
      >
        {status ? status.replace('_', ' ') : 'None'}
      </span>
    );
  };

  const fmtDate = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return '—';
    }
  };

  return (
    <>
      {/* Table styling */}
      <style
        dangerouslySetInnerHTML={{
          __html: `
    .inst-table td { white-space:normal;word-break:break-word;vertical-align:top; }
    .inst-table { table-layout:fixed; }
    .inst-table col.col-name   { width:24%; }
    .inst-table col.col-status { width:11%; }
    .inst-table col.col-sub    { width:12%; }
    .inst-table col.col-stud   { width:8%; }
    .inst-table col.col-quest  { width:8%; }
    .inst-table col.col-exams  { width:8%; }
    .inst-table col.col-renew  { width:12%; }
    .inst-table col.col-acts   { width:17%; }
`,
        }}
      />

      <div className="bg-mesh"></div>

      <div className="main-wrap" style={{ maxWidth: '100%', padding: '24px 28px 80px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '20px',
          }}
        >
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: '800', margin: '0 0 3px' }}>
              Institution Management
            </h1>
            <p style={{ color: 'var(--muted)', margin: '0', fontSize: '0.82rem' }}>
              Activate, suspend, view details and monitor all institutions
            </p>
          </div>
          <button
            className="btn-outline"
            id="refreshBtn"
            onClick={fetchInstitutions}
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{
                width: '14px',
                height: '14px',
                animation: loading ? 'spin 1s linear infinite' : 'none',
              }}
            >
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
            </svg>
            Refresh
          </button>
        </div>

        <div className="section-card">
          <div className="section-body" style={{ paddingBottom: '0' }}>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
              <div className="input-group" style={{ margin: '0' }}>
                <label className="input-label" htmlFor="filterStatus">
                  Status
                </label>
                <select
                  id="filterStatus"
                  className="text-input"
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <option value="">All</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="overdue">Overdue</option>
                  <option value="grace_period">Grace Period</option>
                  <option value="expired">Expired</option>
                </select>
              </div>
            </div>
          </div>

          <div className="section-body" style={{ padding: '0' }}>
            <div className="table-scroll">
              <table className="results-table inst-table">
                <colgroup>
                  <col className="col-name" />
                  <col className="col-status" />
                  <col className="col-sub" />
                  <col className="col-stud" />
                  <col className="col-quest" />
                  <col className="col-exams" />
                  <col className="col-renew" />
                  <col className="col-acts" />
                </colgroup>
                <thead>
                  <tr>
                    <th>Institution</th>
                    <th>Status</th>
                    <th>Subscription</th>
                    <th>Students</th>
                    <th>Questions</th>
                    <th>Exams</th>
                    <th>Renewal</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody id="instTableBody">
                  {loading ? (
                    <tr>
                      <td
                        colSpan="8"
                        style={{ textAlign: 'center', color: 'var(--muted)', padding: '40px' }}
                      >
                        Loading institutions…
                      </td>
                    </tr>
                  ) : error ? (
                    <tr>
                      <td
                        colSpan="8"
                        style={{
                          textAlign: 'center',
                          color: 'var(--red-l, #ef4444)',
                          padding: '36px',
                        }}
                      >
                        ⚠️ {error}
                      </td>
                    </tr>
                  ) : institutions.length === 0 ? (
                    <tr>
                      <td
                        colSpan="8"
                        style={{ textAlign: 'center', color: 'var(--muted)', padding: '40px' }}
                      >
                        No institutions found
                      </td>
                    </tr>
                  ) : (
                    institutions.map((inst) => {
                      const instId = inst.id || inst.institution_id;
                      const subStatus = (inst.subscription_status || 'inactive').toLowerCase();
                      const isActive = ['active', 'trial', 'overdue', 'grace_period'].includes(
                        subStatus
                      );
                      const actionType = isActive ? 'suspend' : 'activate';
                      const actionLabel = isActive ? 'Suspend' : 'Activate';
                      const buttonStyle = isActive
                        ? {
                            color: 'var(--red-l, #ef4444)',
                            borderColor: 'var(--red-l, #ef4444)',
                          }
                        : {
                            color: 'var(--green-l, #10b981)',
                            borderColor: 'var(--green-l, #10b981)',
                          };

                      return (
                        <tr key={instId}>
                          <td>
                            <div style={{ fontWeight: '600', fontSize: '0.87rem' }}>
                              {inst.name}
                            </div>
                            <div
                              style={{
                                fontSize: '0.75rem',
                                color: 'var(--muted)',
                                marginTop: '2px',
                              }}
                            >
                              {inst.contact_phone || 'No phone'}
                              {inst.institution_code && (
                                <span style={{ marginLeft: '8px', opacity: 0.8 }}>
                                  ({inst.institution_code})
                                </span>
                              )}
                            </div>
                          </td>
                          <td>{getStatusBadge(inst.subscription_status)}</td>
                          <td style={{ fontSize: '0.8rem', color: 'var(--muted2)' }}>
                            {inst.plan_name || '—'}
                          </td>
                          <td style={{ textAlign: 'center' }}>{inst.student_count || 0}</td>
                          <td style={{ textAlign: 'center' }}>{inst.question_count || 0}</td>
                          <td style={{ textAlign: 'center' }}>{inst.exam_count || 0}</td>
                          <td style={{ fontSize: '0.8rem' }}>
                            {fmtDate(inst.next_renewal_date)}
                          </td>
                          <td>
                            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                              <button
                                className="btn-outline small"
                                style={{ ...buttonStyle, cursor: 'pointer' }}
                                onClick={() =>
                                  setPendingAction({
                                    action: actionType,
                                    instId,
                                    instName: inst.name,
                                  })
                                }
                              >
                                {actionLabel}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border)' }}>
              <span id="tableFooter" style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                {loading
                  ? 'Loading…'
                  : `${institutions.length} institution${institutions.length === 1 ? '' : 's'}`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {pendingAction && (
        <div
          id="confirmModal"
          style={{
            display: 'flex',
            position: 'fixed',
            inset: '0',
            background: 'rgba(0,0,0,0.6)',
            zIndex: 1000,
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              background: 'var(--card-bg, #1e293b)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r, 8px)',
              padding: '28px',
              maxWidth: '400px',
              width: '90%',
            }}
          >
            <h3 id="confirmTitle" style={{ margin: '0 0 10px', fontSize: '1.05rem' }}>
              {pendingAction.action === 'activate'
                ? 'Activate Institution'
                : 'Suspend Institution'}
            </h3>
            <p
              id="confirmMsg"
              style={{ color: 'var(--muted)', fontSize: '0.88rem', margin: '0 0 20px' }}
            >
              {pendingAction.action === 'activate'
                ? `Activate "${pendingAction.instName}"? This will restore their access to the platform.`
                : `Suspend "${pendingAction.instName}"? Their students and staff will temporarily lose access.`}
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                className="btn-outline small"
                id="confirmCancelBtn"
                disabled={actionLoading}
                onClick={() => setPendingAction(null)}
                style={{ cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                className="btn-primary small"
                id="confirmOkBtn"
                disabled={actionLoading}
                onClick={handleActionConfirm}
                style={{
                  background:
                    pendingAction.action === 'suspend'
                      ? 'var(--red, #dc2626)'
                      : 'var(--primary, #6366f1)',
                  borderColor:
                    pendingAction.action === 'suspend'
                      ? 'var(--red, #dc2626)'
                      : 'var(--primary, #6366f1)',
                  cursor: 'pointer',
                }}
              >
                {actionLoading ? 'Processing…' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AdminInstitutions;
