function getConsents(consent_key) {
    const consent = getCookie(consent_key);
    const json_string = consent ? decodeURIComponent(consent) : '{}'
    return JSON.parse(json_string);
}

function editConsent(consent_key,
                     host,
                     expiration,
                     cookie_domain,
                     cookie_secure=0,
                     revoke=false) {
    if (host) {
        const data = getConsents(consent_key);
        if (!revoke) data[host] = Date.now() + expiration * 24 * 60 * 60 * 1000;
        else data[host] = Date.now() - 1;
        const consentStr = encodeURIComponent(JSON.stringify(data));
        const secure_value = cookie_secure? 'Secure;' : '';
        const expiration_value = expiration * 24 * 60 * 60;
        document.cookie = `${consent_key}=${consentStr};domain=.unical.it;${secure_value}path=/;SameSite=Lax;max-age=${expiration_value}`;
        getCookie(consent_key);
    }
}

function hasConsent(consent_key, host) {
    if (!host) return false;
    const data = getConsents(consent_key);
    return data[host] !== undefined && data[host] > Date.now();
}

//~ function revokeConsent(consent_key, host) {
    //~ if (host) {
        //~ const data = getConsents();
        //~ delete data[host];
        //~ localStorage.setItem(consent_key, JSON.stringify(data));
    //~ }
//~ }

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
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
