import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import './assets/css/style.css'; 
import './assets/css/institution.css';
import './assets/css/subscription.css';
import './assets/css/subscription-modal-premium.css'; 

import AdminLayout from './layouts/AdminLayout';
import StudentLayout from './layouts/StudentLayout';
import InstitutionLayout from './layouts/InstitutionLayout';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Auto-generated components
import AdminAnalytics from './pages/auto/AdminAnalytics';
import AdminDashboard from './pages/auto/AdminDashboard';
import AdminExams from './pages/auto/AdminExams';
import AdminInstitutions from './pages/auto/AdminInstitutions';
import AdminQuestions from './pages/auto/AdminQuestions';
import AdminStudentManage from './pages/auto/AdminStudentManage';
import AdminStudents from './pages/auto/AdminStudents';
import AdminSubscriptions from './pages/auto/AdminSubscriptions';
import AdminSyllabus from './pages/auto/AdminSyllabus';
import AdminTextbookUpload from './pages/auto/AdminTextbookUpload';
import AdminUpload from './pages/auto/AdminUpload';
import Config from './pages/auto/Config';
import ContactUs from './pages/auto/ContactUs';
import Dashboard from './pages/auto/Dashboard';
import Exam from './pages/auto/Exam';
import Index from './pages/auto/Index';
import InstitutionAnalytics from './pages/auto/InstitutionAnalytics';
import InstitutionDashboard from './pages/auto/InstitutionDashboard';
import InstitutionExams from './pages/auto/InstitutionExams';
import InstitutionPricing from './pages/auto/InstitutionPricing';
import InstitutionQuestions from './pages/auto/InstitutionQuestions';
import InstitutionRegister from './pages/auto/InstitutionRegister';
import InstitutionStudents from './pages/auto/InstitutionStudents';
import InstitutionSubscription from './pages/auto/InstitutionSubscription';
import InstitutionSyllabus from './pages/auto/InstitutionSyllabus';
import InstitutionUpload from './pages/auto/InstitutionUpload';
import InvitationAccept from './pages/auto/InvitationAccept';
import Landing from './pages/auto/Landing';
import Login from './pages/auto/Login';
import NotFound from './pages/auto/NotFound';
import Register from './pages/auto/Register';
import StudentInstitutionDashboard from './pages/auto/StudentInstitutionDashboard';
import StudentInstitutionExams from './pages/auto/StudentInstitutionExams';
import StudentInstitutionLeaderboard from './pages/auto/StudentInstitutionLeaderboard';
import StudentInstitutionPerformance from './pages/auto/StudentInstitutionPerformance';
import StudentPricing from './pages/auto/StudentPricing';
import Subscription from './pages/auto/Subscription';
import RazorpaySubscription from './pages/RazorpaySubscription';
import Syllabus from './pages/auto/Syllabus';

// Public Layout Wrapper
const PublicLayout = ({ children }) => (
  <>
    <Navbar role="" links={[{to:'/login', label:'Login'}, {to:'/register', label:'Register'}]} />
    {children}
  </>
);

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<PublicLayout><Landing /></PublicLayout>} />
          <Route path="/index" element={<PublicLayout><Index /></PublicLayout>} />
          <Route path="/login" element={<PublicLayout><LoginPage /></PublicLayout>} />
          <Route path="/register" element={<PublicLayout><RegisterPage /></PublicLayout>} />
          <Route path="/institution/register" element={<PublicLayout><InstitutionRegister /></PublicLayout>} />
          <Route path="/contact-us" element={<PublicLayout><ContactUs /></PublicLayout>} />
          <Route path="/config" element={<Config />} />
          <Route path="/invitation-accept" element={<PublicLayout><InvitationAccept /></PublicLayout>} />

          {/* Student Routes */}
          <Route element={<StudentLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/exam" element={<Exam />} />
            <Route path="/subscription" element={<RazorpaySubscription />} />
            <Route path="/syllabus" element={<Syllabus />} />
            <Route path="/student-pricing" element={<StudentPricing />} />
            
            {/* Institution Specific Student Routes */}
            <Route path="/student-institution-dashboard" element={<StudentInstitutionDashboard />} />
            <Route path="/student-institution-exams" element={<StudentInstitutionExams />} />
            <Route path="/student-institution-leaderboard" element={<StudentInstitutionLeaderboard />} />
            <Route path="/student-institution-performance" element={<StudentInstitutionPerformance />} />
          </Route>

          {/* Admin Routes */}
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="analytics" element={<AdminAnalytics />} />
            <Route path="exams" element={<AdminExams />} />
            <Route path="institutions" element={<AdminInstitutions />} />
            <Route path="questions" element={<AdminQuestions />} />
            <Route path="student-manage" element={<AdminStudentManage />} />
            <Route path="students" element={<AdminStudents />} />
            <Route path="subscriptions" element={<AdminSubscriptions />} />
            <Route path="syllabus" element={<AdminSyllabus />} />
            <Route path="textbook-upload" element={<AdminTextbookUpload />} />
            <Route path="upload" element={<AdminUpload />} />
          </Route>

          {/* Institution Routes */}
          <Route path="/institution" element={<InstitutionLayout />}>
            <Route index element={<Navigate to="/institution/dashboard" replace />} />
            <Route path="analytics" element={<InstitutionAnalytics />} />
            <Route path="dashboard" element={<InstitutionDashboard />} />
            <Route path="exams" element={<InstitutionExams />} />
            <Route path="pricing" element={<InstitutionPricing />} />
            <Route path="questions" element={<InstitutionQuestions />} />
            <Route path="students" element={<InstitutionStudents />} />
            <Route path="subscription" element={<InstitutionSubscription />} />
            <Route path="syllabus" element={<InstitutionSyllabus />} />
            <Route path="upload" element={<InstitutionUpload />} />
          </Route>

          {/* Fallback route */}
          <Route path="*" element={<PublicLayout><NotFound /></PublicLayout>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
