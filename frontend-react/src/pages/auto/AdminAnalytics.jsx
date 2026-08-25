import React from 'react';
import { Link } from 'react-router-dom';

const AdminAnalytics = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  <main className="dash-main">
    
    <div className="dash-hero">
      <div>
        <h1 className="dash-title">Admin <span className="hero-gradient">Analytics</span></h1>
        <p className="dash-sub">Aggregate performance analytics across all students and subjects</p>
      </div>
      <div className="dash-hero-right">
        <div className="last-updated" id="lastUpdated">Last updated: —</div>
        <button className="btn-outline" >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>
          Refresh
        </button>
        <button className="btn-primary small" id="exportBtn" >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Export CSV
        </button>
      </div>
    </div>

    
    <div className="empty-state" id="emptyState" style={{"display":"none"}}>
      <div className="empty-icon">📊</div>
      <h3>No Submissions Found</h3>
      <p>No submissions match the current filter criteria. Try adjusting the filters above.</p>
    </div>

    <div id="dashContent">
      
      <div className="dash-filters section-card">
        <div className="filter-row">
          <div className="filter-group">
            <label className="input-label">Student</label>
            <select id="filterStudent" className="select-input" >
              <option value="all">All Students</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Subject</label>
            <select id="filterSubject" className="select-input" >
              <option value="all">All Subjects</option>
              <option value="Biology">Biology</option>
              <option value="Physics">Physics</option>
              <option value="Chemistry">Chemistry</option>
              <option value="Mathematics">Mathematics</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Paper Set</label>
            <select id="filterSet" className="select-input" >
              <option value="all">All Sets</option>
            </select>
          </div>
          <div className="filter-group">
            <label className="input-label">Status</label>
            <select id="filterStatus" className="select-input" >
              <option value="all">All</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
            </select>
          </div>
        </div>
      </div>

      
      <div className="kpi-row" id="kpiRow">
        <div className="kpi-tile">
          <div className="kpi-tile-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiStudents">0</div>
            <div className="kpi-tile-label">Total Students</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiSubmissions">0</div>
            <div className="kpi-tile-label">Submissions</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiAvgScore">0%</div>
            <div className="kpi-tile-label">Avg Score</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiPassRate">0%</div>
            <div className="kpi-tile-label">Pass Rate</div>
          </div>
        </div>
        <div className="kpi-tile">
          <div className="kpi-tile-icon orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div className="kpi-tile-body">
            <div className="kpi-tile-val" id="kpiAvgTime">0m</div>
            <div className="kpi-tile-label">Avg Time</div>
          </div>
        </div>
      </div>

      
      <div className="charts-row">
        <div className="chart-card section-card wide">
          <div className="chart-card-header">
            <h3>Score Distribution</h3>
          </div>
          <div className="chart-wrap"><canvas id="scoreDistChart"></canvas></div>
        </div>
      </div>

      
      <div className="charts-row" style={{"marginTop":"20px"}}>
        <div className="chart-card section-card">
          <div className="chart-card-header"><h3>Subject-wise Avg Score</h3></div>
          <div className="chart-wrap"><canvas id="subjectChart"></canvas></div>
        </div>
        <div className="chart-card section-card">
          <div className="chart-card-header"><h3>Pass vs Fail</h3></div>
          <div className="chart-wrap"><canvas id="passChart"></canvas></div>
        </div>
      </div>

      
      <div className="section-card results-card" style={{"marginTop":"20px"}}>
        <div className="results-header">
          <h3>🏆 Student Leaderboard</h3>
        </div>
        
        <div className="chart-wrap" style={{"height":"280px","padding":"16px"}}>
          <canvas id="leaderboardChart"></canvas>
        </div>
        
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Student</th>
                <th>KCET ID</th>
                <th>Composite Score</th>
                <th>Avg Score</th>
                <th>Attempts</th>
              </tr>
            </thead>
            <tbody id="leaderboardBody"></tbody>
          </table>
        </div>
      </div>

      
      <div className="section-card results-card" style={{"marginTop":"20px"}}>
        <div className="results-header">
          <h3>Student Results</h3>
          <div className="results-search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="text" id="searchInput" className="search-input" placeholder="Search student..." />
          </div>
        </div>
        <div className="table-scroll">
          <table className="results-table">
            <thead>
              <tr>
                <th >Student <span className="sort-icon">↕</span></th>
                <th>KCET ID</th>
                <th >Subject <span className="sort-icon">↕</span></th>
                <th >Set <span className="sort-icon">↕</span></th>
                <th >Score <span className="sort-icon">↕</span></th>
                <th >Time <span className="sort-icon">↕</span></th>
                <th >Status <span className="sort-icon">↕</span></th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="resultsBody"></tbody>
          </table>
        </div>
        <div className="table-footer" id="tableFooter"></div>
      </div>
    </div>
  </main>

  
  <div className="drawer-overlay" id="drawerOverlay"  style={{"display":"none"}}></div>
  <div className="detail-drawer" id="detailDrawer">
    <div className="drawer-header">
      <div>
        <h3 id="drawerName">Student Name</h3>
        <p className="drawer-meta" id="drawerMeta"></p>
      </div>
      <button className="drawer-close" >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div className="drawer-body" id="drawerBody"></div>
  </div>

  
  
  

    </>
  );
};

export default AdminAnalytics;
