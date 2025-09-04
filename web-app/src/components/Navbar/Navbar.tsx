import { Link } from 'react-router-dom';
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
                    <button>
                        طريقة الاستخدام
                    </button>
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