const cookie_data = document.getElementById('unicms-cookie-data');
const external_sources_consent_key = cookie_data.dataset.external_sources_consent_key;
const external_sources_consent_key_expiration = cookie_data.dataset.external_sources_consent_key_expiration;
const cookie_domain = cookie_data.dataset.cookie_domain;


function getConsents() {
    const consent = getCookie();
    try {
        const json_string = consent ? decodeURIComponent(consent) : '{}';
        return JSON.parse(json_string);
    } catch {
        return {};
    }
}

function editConsent(host, revoke=false) {
    if (host) {
        const data = getConsents();
        if (!revoke) data[host] = Date.now() + external_sources_consent_key_expiration * 24 * 60 * 60 * 1000;
        else data[host] = Date.now() - 1;
        const consentStr = encodeURIComponent(JSON.stringify(data));
        const expiration_value = external_sources_consent_key_expiration * 24 * 60 * 60;
        const secure_value = window.location.protocol === "https:" ? "Secure;" : "";
        document.cookie = `${external_sources_consent_key}=${consentStr};domain=.unical.it;${secure_value}path=/;SameSite=Lax;max-age=${expiration_value}`;
        getCookie();
    }
}

function hasConsent(host) {
    if (!host) return false;
    if (window.location.host.split(":")[0].endsWith(host)) return true;
    const data = getConsents();
    return data[host] !== undefined && data[host] > Date.now();
}

function getCookie() {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${external_sources_consent_key}=`);
    if (parts.length === 2) {
        const encoded_value = parts.pop().split(";").shift();
        return encoded_value;
    }
    return null;
}

function normalizeHost(urlString) {
    try {
        const host = new URL(urlString).hostname.replace(/^www\./, "");
        return host;
    } catch {
        return null;
    }
}
