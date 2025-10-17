const cookie_data = JSON.parse(document.getElementById('unicms-cookie-data').textContent);
const external_sources_consent_key = cookie_data.external_sources_consent_key;
const external_sources_consent_key_expiration = cookie_data.external_sources_consent_key_expiration;
const cookie_domain = cookie_data.cookie_domain;


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
    return tldts.parse(urlString).domain;
}

function getConsents() {
    const consent = getCookie();
    try {
        const json_string = consent ? decodeURIComponent(consent) : '{}';
        const data = JSON.parse(json_string);
        const to_delete = [];
        for (const host in data) {
            if (!normalizeHost(host)) to_delete.push(key);
        }
        for (const del in to_delete) {
            delete data[del];
        }
        return data;
    } catch {
        return {};
    }
}

function editConsent(host, revoke=false) {
    if (!host) return;
    const norm_host = normalizeHost(host)
    const main_domain = normalizeHost(window.location.host)
    const data = getConsents();
    if (!revoke) data[norm_host] = Date.now() + external_sources_consent_key_expiration * 24 * 60 * 60 * 1000;
    else data[norm_host] = Date.now() - 1;
    const consentStr = encodeURIComponent(JSON.stringify(data));
    const expiration_value = external_sources_consent_key_expiration * 24 * 60 * 60;
    const secure_value = window.location.protocol === "https:" ? "Secure;" : "";
    document.cookie = `${external_sources_consent_key}=${consentStr};domain=.${main_domain};${secure_value}path=/;SameSite=Lax;max-age=${expiration_value}`;
    getCookie();
}

function hasConsent(url) {
    if (!url) return false;
    const host = normalizeHost(url);
    if (!host) return false;
    if (window.location.host.split(":")[0].endsWith(host)) return true;
    const data = getConsents();
    return data[host] !== undefined && data[host] > Date.now();
}

