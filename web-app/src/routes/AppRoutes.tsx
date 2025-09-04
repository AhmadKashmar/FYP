import { Routes, Route } from "react-router-dom";
import { Home } from "../pages/Home";
import ContactUs from "../pages/ContactUs";

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/contactus" element={<ContactUs/>} />
    </Routes>
  );
};
