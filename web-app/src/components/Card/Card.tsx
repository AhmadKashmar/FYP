import './card.css';

type CardProps = {
  title: string;
  text: string;
  additionalInfo?: string[]; // the first element will be the title of the additional info
  links?: string[];  // the first element will be the title of the links
};

const Card = ({ title, text, additionalInfo, links }: CardProps) => {
  return (
    <div className="card">
      <h2>{title}</h2>
      <p>{text}</p>
      {additionalInfo && additionalInfo.length > 0 && (
        <p>
          <strong>{additionalInfo[0]}</strong>
          {additionalInfo.slice(1).map((info, index) => (
            <div key={index}>
              <p> {info}</p>
            </div>
          ))}
        </p>
      )}
      {links && links.length > 0 && (
        <p>
          <strong>{links[0]}</strong>
          {links.slice(1).map((link, index) => (
            <div key={index}>
              <a href={link}>{link}</a>
            </div>
          ))}
        </p>
      )}
    </div>
  );
};

export default Card;