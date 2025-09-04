import Card from '../components/Card/Card';

const phoneNumbers = [
    "🖁هاتف:",
    "(+961) 81457080",
    "(+961) 03756521"
  ];

  const emailLinks = [
    "✉︎البريد الإلكتروني:",
    "mailto:mhmdhsenmalli123@gmail.com",
    "mailto:ahmadkashmar999@gmail.com"
  ];

const ContactUs = () => {
    return (
    <div style={{ textAlign: 'center', direction: 'rtl' }}>
      <h1>مرحباً بكم</h1>
      <p>هنا ستجد معلومات الاتصال الخاصة بنا.</p>
      <Card 
      title="🗪 تواصل معنا"
        text="نحن هنا لمساعدتك. لا تتردد في التواصل معنا عبر الهاتف أو البريد الإلكتروني."
        additionalInfo={phoneNumbers}
        links={emailLinks}
      />
    </div>
  );
}

export default ContactUs;