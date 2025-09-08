import React, { useState } from "react";
import { steps } from "../../util/constants";
import "./modal.css";

const GuideModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const changeStep = (newStep: number) => {
    setIsAnimating(true);
    setTimeout(() => {
      setStep(newStep);
      setIsAnimating(false);
    }, 250);
  };

  return (
    <>
      <button
        onClick={() => {
          setIsOpen(true);
          setStep(0);
        }}
      >
        طريقة الاستخدام
      </button>

      {isOpen && (
        <div className="guide-overlay">
          <div className="guide-modal" dir="rtl">
            <div className={`guide-content ${isAnimating ? "fade" : ""}`}>
              <h2>{steps[step].title}</h2>
              <p>{steps[step].text}</p>
               {steps[step].image && <img
                src={steps[step].image}
                alt={steps[step].title}
                style={{ maxWidth: "100%", borderRadius: "8px", marginTop: "10px" }}
              />}
            </div>

            <div className="guide-actions">
              <button onClick={() => setIsOpen(false)}>
                إغلاق
              </button>
              <div className="step-btns">
                {step > 0 && (
                  <button onClick={() => changeStep(step - 1)}>
                    السابق
                  </button>
                )}
                {step < steps.length - 1 ? (
                  <button onClick={() => changeStep(step + 1)}>
                    التالي
                  </button>
                ) : (
                  <button onClick={() => setIsOpen(false)}>
                    إنهاء
                  </button>
                )}
              </div>
            </div>

            <div className="progress-dots">
              {steps.map((_, idx) => (
                <span key={idx} className={`dot ${idx === step ? "active" : ""}`} />
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GuideModal;
