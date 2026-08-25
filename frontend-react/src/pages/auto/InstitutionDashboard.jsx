import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const InstitutionDashboard = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    // Simulate API fetch for Institution Dashboard Data
    setTimeout(() => {
      // Remove loading state by styling the display block appropriately
      const loader = document.getElementById('dashboardLoading');
      const content = document.getElementById('dashboardContent');
      if (loader) loader.style.display = 'none';
      if (content) content.style.display = 'block';

      setData({
        kpis: {
          students: 350,
          testsWeek: 12,
          testsMonth: 48,
          status: 'Active'
        }
      });
    }, 800);
  }, []);

  const chartOptions = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { color: '#64748b' } },
      x: { grid: { display: false }, ticks: { color: '#64748b' } }
    }
  };

  const performanceChartData = {
    labels: ['Physics', 'Chemistry', 'Math', 'Bio'],
    datasets: [{
      label: 'Average Score',
      data: [75, 82, 65, 88],
      backgroundColor: 'rgba(124, 58, 237, 0.8)',
      borderRadius: 4
    }]
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      <div className="bg-mesh"></div>
      
      <main className="institution-page" id="institutionDashboardPage">
    
    <div className="institution-page-header">
      <div>
        <h1 className="institution-page-title">
          Institution <span className="institution-page-title-accent">Dashboard</span>
        </h1>
        <p className="institution-page-sub" id="institutionName">Overview of your institution's activity and subscription</p>
      </div>
      <div className="institution-page-header-actions">
        <div className="last-updated" id="lastUpdated" role="status" aria-live="polite" aria-atomic="true">Last updated: —</div>
        <button className="btn-institution-outline" id="refreshDashboardBtn" type="button" aria-label="Refresh dashboard data">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
      </div>
    </div>

    
    <div className="institution-alert-banner" id="subscriptionAlertBanner" role="alert" aria-live="polite" style={{"display":"none"}}>
      <div className="alert-content">
        <span className="alert-icon" aria-hidden="true">⚠️</span>
        <div className="alert-text">
          <strong id="alertTitle">Payment Overdue</strong>
          <span id="alertMessage">Your institution's access will be suspended soon.</span>
        </div>
      </div>
      <Link to="/institution/subscription" className="btn-institution" id="alertActionBtn" aria-describedby="alertTitle alertMessage">Pay Now</Link>
    </div>

    
    <div className="loading-state" id="dashboardLoading" role="status" aria-live="polite">
      <div className="loading-spinner" aria-hidden="true"></div>
      <p>Loading dashboard...</p>
    </div>

    
    <div className="empty-state" id="dashboardError" style={{"display":"none"}} role="alert" aria-live="polite">
      <div className="empty-icon" aria-hidden="true">⚠️</div>
      <h3>Unable to load dashboard data</h3>
      <p id="dashboardErrorMessage">Please check your connection and try again.</p>
      <div className="empty-actions">
        <button className="btn-institution" id="retryDashboardBtn" type="button" aria-label="Retry loading dashboard">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Retry
        </button>
      </div>
    </div>

    
    <div id="dashboardContent" style={{"display":"none"}}>

      
      <section className="kpi-grid" aria-label="Institution key metrics">
        
        <div className="kpi-tile" id="kpiTileStudents">
          <div className="kpi-icon" aria-hidden="true">👥</div>
          <div className="kpi-value" id="kpiTotalStudents">{data ? data.kpis.students : "—"}</div>
          <div className="kpi-label">Total Students</div>
        </div>

        
        <div className="kpi-tile" id="kpiTileWeek">
          <div className="kpi-icon" aria-hidden="true">📝</div>
          <div className="kpi-value" id="kpiTestsThisWeek">{data ? data.kpis.testsWeek : "—"}</div>
          <div className="kpi-label">Tests This Week</div>
        </div>

        
        <div className="kpi-tile" id="kpiTileMonth">
          <div className="kpi-icon" aria-hidden="true">📊</div>
          <div className="kpi-value" id="kpiTestsThisMonth">{data ? data.kpis.testsMonth : "—"}</div>
          <div className="kpi-label">Tests This Month</div>
        </div>

        
        <div className="kpi-tile" id="kpiTileStatus" data-status="active">
          <div className="kpi-icon" aria-hidden="true">✓</div>
          <div className="kpi-value" id="kpiSubscriptionStatus" role="status" aria-live="polite">{data ? data.kpis.status : "—"}</div>
          <div className="kpi-label">Subscription Status</div>
        </div>
      </section>

      
      

      
      <section className="section-card" aria-labelledby="recentActivityHeading">
        <div className="section-card-header">
          <div className="section-icon institution" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
          </div>
          <div>
            <h2 id="recentActivityHeading">Recent Activity</h2>
            <p className="section-sub">10 most recent exam submissions by your students</p>
          </div>
        </div>
        <div className="section-body">
          
          <div className="recent-activity-empty" id="recentActivityEmpty" style={{"display":"none"}} role="status" aria-live="polite">
            <p className="empty-message">No exam submissions yet. Activity will appear here as students take tests.</p>
          </div>

          
          <div className="responsive-table-wrapper" id="recentActivityWrapper">
            <table className="results-table" id="recentActivityTable" aria-describedby="recentActivityHeading">
              <thead>
                <tr>
                  <th scope="col">Student</th>
                  <th scope="col">Subject</th>
                  <th scope="col">Score</th>
                  <th scope="col">Date</th>
                  <th scope="col">Time Taken</th>
                </tr>
              </thead>
              <tbody id="recentActivityBody">
                
              </tbody>
            </table>
          </div>
        </div>
      </section>

      
      <section className="section-card chart-card" aria-labelledby="performanceSummaryHeading">
        <div className="section-card-header">
          <div className="section-icon institution" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          </div>
          <div>
            <h2 id="performanceSummaryHeading">Student Performance Summary</h2>
            <p className="section-sub">Average score by subject across all institution students</p>
          </div>
        </div>
        <div className="section-body">
          
          <div className="performance-empty" id="performanceEmpty" style={{"display":"none"}} role="status" aria-live="polite">
            <p className="empty-message">No performance data available yet. Charts will appear once students submit exams.</p>
          </div>
          
          <div className="chart-wrap" id="performanceChartWrap">
            <div style={{ height: "300px" }}>{data && <Bar data={performanceChartData} options={chartOptions} />}</div>
          </div>
        </div>
      </section>
    </div>

    
    <div className="modal-overlay" id="studentsModal" role="dialog" aria-modal="true" aria-labelledby="studentsModalTitle" aria-hidden="true" style={{"display":"none"}}>
      <div className="modal-dialog" style={{"maxWidth":"900px"}}>
        <div className="modal-header">
          <h2 id="studentsModalTitle">All Students</h2>
          <button type="button" className="modal-close" id="studentsModalClose" aria-label="Close students list">&times;</button>
        </div>
        <div className="modal-body" style={{"maxHeight":"70vh","overflowY":"auto"}}>
          
          <div id="institutionStudentsSection">
            <h3 id="institutionName" style={{"marginTop":"0","color":"var(--purple-l, #a78bfa)","fontSize":"1.1rem"}}>Loading...</h3>
            <p style={{"color":"var(--muted)","marginBottom":"16px"}}>Institution-Linked Students</p>
            <div className="responsive-table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Student ID</th>
                  </tr>
                </thead>
                <tbody id="institutionStudentsBody">
                  <tr><td colspan="3" style={{"textAlign":"center","color":"var(--muted)","padding":"20px"}}>Loading...</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          
          <div id="directSubscribersSection" style={{"marginTop":"32px"}}>
            <h3 style={{"marginTop":"0","color":"var(--green-l, #86efac)","fontSize":"1.1rem"}}>Direct Subscribers</h3>
            <p style={{"color":"var(--muted)","marginBottom":"16px"}}>All Platform Direct Subscribers</p>
            <div className="responsive-table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Email</th>
                    <th scope="col">Student ID</th>
                  </tr>
                </thead>
                <tbody id="directSubscribersBody">
                  <tr><td colspan="3" style={{"textAlign":"center","color":"var(--muted)","padding":"20px"}}>Loading...</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          
          <div style={{"marginTop":"24px","padding":"16px","background":"rgba(167, 139, 250, 0.08)","borderRadius":"8px","border":"1px solid var(--border)"}}>
            <p style={{"margin":"0","color":"var(--text)","fontWeight":"500"}}>
              <span id="institutionStudentCount">0</span> institution students + <span id="directSubscriberCount">0</span> direct subscribers = <span id="totalStudentCount">0</span> total students
            </p>
          </div>
        </div>
      </div>
    </div>

  </main>
    </>
  );
};

export default InstitutionDashboard;
