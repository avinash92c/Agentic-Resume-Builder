// import { Routes, Route, Navigate } from 'react-router-dom';
// import PersonalInfoForm from '../components/PersonalInfoForm';
// import EducationForm from '../components/EducationForm';
// import CertificationsForm from '../components/CertificationsForm';
// import Chat from '../components/Chat';

// const AppRouter = () => {
//     return (
//         <Routes>
//             <Route path="/" element={<Navigate to="/personal-info" />} />
//             <Route path="/personal-info" element={<PersonalInfoForm />} />
//             <Route path="/education" element={<EducationForm />} />
//             <Route path="/certifications" element={<CertificationsForm />} />
//             <Route path="/work-experience" element={<Chat />} />
//             <Route path="/professional-summary" element={<Chat />} />
//             <Route path="/skills" element={<Chat />} />
//             <Route path="/review" element={<Chat />} />
//             <Route path="/cover-letter" element={<Chat />} />
//             <Route path="/job-fit" element={<Chat />} />
//             <Route path="/assessment" element={<Chat />} />
//             <Route path="/learning-roadmap" element={<Chat />} />
//         </Routes>
//     );
// };

// export default AppRouter;

import { Routes, Route, Navigate } from 'react-router-dom';

import PersonalInfoForm from '../components/PersonalInfoForm';
import EducationForm from '../components/EducationForm';
import CertificationsForm from '../components/CertificationsForm';

import AgentChatPage from '../components/AgentChatPage';
import WorkHistoryForm from '../components/WorkHistoryForm';

const AppRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/personal-info" />} />

            <Route
                path="/personal-info"
                element={<PersonalInfoForm />}
            />

            <Route
                path="/education"
                element={<EducationForm />}
            />

            <Route
                path="/certifications"
                element={<CertificationsForm />}
            />

            <Route
                path="/professional-summary"
                element={<AgentChatPage agent="psg" />}
            />

            <Route
                path="/work-experience"
                element={<WorkHistoryForm />}
            />

            <Route
                path="/personal-projects"
                element={<AgentChatPage agent="pp" />}
            />

            <Route
                path="/review"
                element={<AgentChatPage agent="fd" />}
            />
        </Routes>
    );
};

export default AppRouter;