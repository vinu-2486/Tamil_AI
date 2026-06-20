import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "../styles/landing.css";

type Lang = "en" | "ta";
type Theme = "dark" | "light";

const STRINGS: Record<Lang, Record<string, string>> = {
  en: {
    brand: "கற்பது தமிழ், கற்பிப்பது AI",
    eyebrow: "Voice-based Tamil pronunciation coach",
    tagline:
      "Speak Tamil. Get instant, slang-aware feedback on your pronunciation — and a score that tells you exactly how close you got.",
    cta_primary: "Get started",
    cta_secondary: "See how it works",
    how_kicker: "The process",
    how_title: "Three steps, one sentence",
    how_sub: "No setup, no account walls. Open the mic and start practicing.",
    step1_title: "Record your voice",
    step1_desc: "Speak a Tamil sentence into your mic — no setup needed.",
    step2_title: "Get transcribed & scored",
    step2_desc: "We transcribe what you said and score your pronunciation accuracy.",
    step3_title: "Hear coached corrections",
    step3_desc: "Listen to AI-generated coach feedback and the correct pronunciation.",
    adv_kicker: "Why this, not a phrasebook",
    adv_title: "Built for how Tamil is actually spoken",
    adv_sub: "Designed around real speech, not just textbook pronunciation.",
    adv1_title: "Slang-aware feedback",
    adv1_desc: "Understands regional Tamil slang, not just textbook pronunciation.",
    adv2_title: "Instant accuracy score",
    adv2_desc: "Know exactly how close you are, out of 100, right after you speak.",
    adv3_title: "Bilingual coaching",
    adv3_desc: "Get feedback in English or Tamil — your choice.",
    adv4_title: "Practice anytime",
    adv4_desc: "No classroom, no schedule. Just open the app and speak.",
    band_title: "Ready to hear how you actually sound?",
    band_sub: "It takes one sentence to get your first score.",
    footer_text: "கற்பது தமிழ், கற்பிப்பது AI — built for learners, by learners.",
  },
  ta: {
    brand: "கற்பது தமிழ், கற்பிப்பது AI",
    eyebrow: "குரல் வழி தமிழ் உச்சரிப்பு பயிற்சியாளர்",
    tagline:
      "தமிழில் பேசுங்கள். உங்கள் பேச்சு பாணிக்கேற்ப உடனடி பின்னூட்டமும், எவ்வளவு துல்லியமாக பேசினீர்கள் என்பதைக் காட்டும் மதிப்பெண்ணும் பெறுங்கள்.",
    cta_primary: "தொடங்குங்கள்",
    cta_secondary: "எப்படி வேலை செய்கிறது எனப் பாருங்கள்",
    how_kicker: "செயல்முறை",
    how_title: "மூன்று படிகள், ஒரு வாக்கியம்",
    how_sub: "அமைப்பு தேவையில்லை, கணக்கு தேவையில்லை. மைக்கைத் திறந்து பயிற்சியைத் தொடங்குங்கள்.",
    step1_title: "உங்கள் குரலைப் பதிவு செய்யுங்கள்",
    step1_desc: "மைக்கில் ஒரு தமிழ் வாக்கியத்தைப் பேசுங்கள் — எந்த அமைப்பும் தேவையில்லை.",
    step2_title: "எழுத்துருவாக்கி, மதிப்பெண் பெறுங்கள்",
    step2_desc: "நீங்கள் பேசியதை எழுத்துருவாக்கி, உச்சரிப்பு துல்லியத்தை மதிப்பிடுகிறோம்.",
    step3_title: "பயிற்சியான திருத்தங்களைக் கேளுங்கள்",
    step3_desc: "AI பயிற்சியாளர் கருத்துகளையும் சரியான உச்சரிப்பையும் கேளுங்கள்.",
    adv_kicker: "இது ஏன், ஒரு சொற்றொடர் புத்தகம் அல்ல",
    adv_title: "தமிழ் உண்மையில் பேசப்படும் விதத்திற்காக உருவாக்கப்பட்டது",
    adv_sub: "பாடப் புத்தக உச்சரிப்பு மட்டுமல்ல, இயல்பான பேச்சுக்கேற்ப வடிவமைக்கப்பட்டது.",
    adv1_title: "பேச்சு வழக்கை உணரும் பின்னூட்டம்",
    adv1_desc: "பாடப் புத்தக உச்சரிப்பு மட்டுமல்ல, பிராந்திய பேச்சு வழக்கையும் புரிந்துகொள்கிறது.",
    adv2_title: "உடனடி துல்லிய மதிப்பெண்",
    adv2_desc: "நீங்கள் பேசியவுடன், 100க்கு எவ்வளவு துல்லியமாக பேசினீர்கள் என்பதை அறியுங்கள்.",
    adv3_title: "இருமொழி பயிற்சி",
    adv3_desc: "ஆங்கிலத்திலோ தமிழிலோ பின்னூட்டம் பெறுங்கள் — உங்கள் விருப்பம்.",
    adv4_title: "எப்போது வேண்டுமானாலும் பயிற்சி",
    adv4_desc: "வகுப்பறை இல்லை, நேரம் குறிப்பிட வேண்டாம். ஆப்பைத் திறந்து பேசுங்கள்.",
    band_title: "நீங்கள் உண்மையில் எப்படி பேசுகிறீர்கள் எனக் கேட்க தயாரா?",
    band_sub: "உங்கள் முதல் மதிப்பெண்ணைப் பெற ஒரே ஒரு வாக்கியம் போதும்.",
    footer_text: "கற்பது தமிழ், கற்பிப்பது AI — கற்பவர்களால், கற்பவர்களுக்காக உருவாக்கப்பட்டது.",
  },
};

const STEP_KEYS = ["step1", "step2", "step3"] as const;
const ADV_KEYS = ["adv1", "adv2", "adv3", "adv4"] as const;

export default function Landing() {
  const [lang, setLang] = useState<Lang>("en");
  const [theme, setTheme] = useState<Theme>("dark");
  const revealRef = useRef<HTMLDivElement>(null);
  const t = STRINGS[lang];

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    const root = revealRef.current;
    if (!root) return;

    const els = root.querySelectorAll(".step-card, .adv-card");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );

    els.forEach((el, i) => {
      (el as HTMLElement).style.transitionDelay = `${(i % 4) * 0.08}s`;
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="lp" ref={revealRef}>
      <nav>
        <div className="wrap">
          <div className="brand">
            <svg className="mark" viewBox="0 0 26 26">
              <circle className="d" cx="13" cy="3" r="2.3" />
              <circle className="d" cx="21" cy="8" r="2.3" />
              <circle className="d" cx="21" cy="18" r="2.3" />
              <circle className="d" cx="13" cy="23" r="2.3" />
              <circle className="d" cx="5" cy="18" r="2.3" />
              <circle className="d" cx="5" cy="8" r="2.3" />
            </svg>
            <span className="full">{t.brand}</span>
            <span className="short">KTKA</span>
          </div>
          <div className="nav-controls">
            <div className="pill-toggle">
              <button
                className={lang === "en" ? "active" : ""}
                onClick={() => setLang("en")}
              >
                EN
              </button>
              <button
                className={lang === "ta" ? "active" : ""}
                onClick={() => setLang("ta")}
              >
                த
              </button>
            </div>
            <button
              className="icon-btn"
              aria-label="Toggle theme"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </nav>

      <section className="hero">
        <svg className="kolam-bg" viewBox="0 0 200 200">
          <path
            className="line"
            d="M100,15 C140,15 185,40 185,80 C185,120 160,160 120,180 C90,195 50,190 25,165 C5,145 5,105 25,75 C45,45 80,15 100,15 Z"
          />
          <circle className="pt" style={{ animationDelay: "0.3s" }} cx="100" cy="15" r="3.5" />
          <circle className="pt" style={{ animationDelay: "0.6s" }} cx="185" cy="80" r="3.5" />
          <circle className="pt" style={{ animationDelay: "0.9s" }} cx="120" cy="180" r="3.5" />
          <circle className="pt" style={{ animationDelay: "1.2s" }} cx="25" cy="165" r="3.5" />
          <circle className="pt" style={{ animationDelay: "1.5s" }} cx="25" cy="75" r="3.5" />
          <circle className="pt" style={{ animationDelay: "1.8s" }} cx="100" cy="15" r="3.5" />
        </svg>

        <div className="wrap">
          <div className="eyebrow">
            <span className="dot"></span> {t.eyebrow}
          </div>
          <h1>{t.brand}</h1>
          <p className={`tagline ${lang === "ta" ? "tamil" : ""}`}>{t.tagline}</p>
          <div className="hero-ctas">
            <Link className="btn primary" to="/practice">
              <span>{t.cta_primary}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
            <a className="btn" href="#how-it-works">
              <span>{t.cta_secondary}</span>
            </a>
          </div>
        </div>
      </section>

      <section id="how-it-works">
        <div className="wrap">
          <div className="section-head">
            <div className="kicker">{t.how_kicker}</div>
            <h2>{t.how_title}</h2>
            <p>{t.how_sub}</p>
          </div>
          <div className="steps">
            {STEP_KEYS.map((key, i) => (
              <div className="step-card" key={key}>
                <div className="step-num">{`0${i + 1}`}</div>
                <h3>{t[`${key}_title`]}</h3>
                <p>{t[`${key}_desc`]}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="advantages">
        <div className="wrap">
          <div className="section-head">
            <div className="kicker">{t.adv_kicker}</div>
            <h2>{t.adv_title}</h2>
            <p>{t.adv_sub}</p>
          </div>
          <div className="adv-grid">
            {ADV_KEYS.map((key) => (
              <div className="adv-card" key={key}>
                <div className="adv-icon">
                  <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 7v5l3 1.5" />
                  </svg>
                </div>
                <div>
                  <h3>{t[`${key}_title`]}</h3>
                  <p>{t[`${key}_desc`]}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="wrap">
          <div className="cta-band">
            <h2>{t.band_title}</h2>
            <p>{t.band_sub}</p>
            <Link className="btn primary" to="/practice">
              <span>{t.cta_primary}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      <footer>
        <div className="kolam-divider">
          <span></span><span></span><span></span><span></span><span></span><span></span><span></span>
        </div>
        <p>{t.footer_text}</p>
      </footer>
    </div>
  );
}