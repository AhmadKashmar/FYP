import { Link } from 'react-router-dom';
import GuideModal from '../GuideModal/GuideModal';
import "./navbar.css";

const Navbar = () => {
    return (
        <header className="App-header">
            <img src={"/assets/logo.png"} alt="logo"/>
            <nav>
                <Link to="/">
                    <button>
                        الرئيسية
                    </button>
                </Link>
                    <GuideModal/>
                <Link to="/contactus">
                    <button>
                        تواصل معنا
                    </button>
                </Link>
            </nav>
        </header>
    );
}

export default Navbar;