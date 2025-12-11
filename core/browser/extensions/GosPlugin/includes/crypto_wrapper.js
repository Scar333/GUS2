let _originalCrypto;
let _wrapperCrypto;

function wrap(wrappee) {
    if (typeof wrappee === 'undefined') {
        return;
    }

    const OID_MAP = {
        "2.5.4.12": "T", "2.5.4.3": "CN", "2.5.4.11": "OU", "2.5.4.4": "SN",
        "2.5.4.42": "G", "1.2.840.113549.1.9.1": "E", "1.2.643.100.3": "SNILS",
        "2.5.4.10": "O", "1.2.643.3.131.1.1": "INN", "1.2.643.100.4": "INNLE",
        "1.2.643.3.61.502710.1.7": "KPP", "1.2.643.100.1": "OGRN", "1.2.643.100.5": "OGRNIP",
        "2.5.4.9": "STREET", "2.5.4.8": "ST", "2.5.4.7": "L", "2.5.4.6": "C"
    };

    const formatOids = (row) => String(row)
        .split(";")
        .map(pair => {
            let [key, value] = pair.split("=");
            return `${OID_MAP[key] || key}=${value}`;
        })
        .join(";");

    const formatTimestamp = (timestamp) => timestamp ? new Date(timestamp * 1000).toISOString() : "";

    const format = (entity) => {
        if (!entity) return entity;
        entity.validPeriod = {
            from: formatTimestamp(entity.notBefore),
            to: formatTimestamp(entity.notAfter)
        };
        delete entity.notBefore;
        delete entity.notAfter;

        entity.privateKeyPeriod = {
            from: formatTimestamp(entity.privateKeyNotBefore),
            to: formatTimestamp(entity.privateKeyNotAfter)
        };
        delete entity.privateKeyNotBefore;
        delete entity.privateKeyNotAfter;

        if (entity.issuer) {
            entity.issuerInfo = formatOids(entity.issuer);
            delete entity.issuer;
        }
        if (entity.subject) {
            entity.subjectInfo = formatOids(entity.subject);
            delete entity.subject;
        }
        return entity;
    };

    const handle = (message, formatter) => {
        if (message.method.result) {
            let parsed = JSON.parse(message.method.result);
            message.method.result = JSON.stringify(formatter(parsed));
        }
    };

    let _profile = null;

    _originalCrypto = wrappee;
    _wrapperCrypto = { ..._originalCrypto };

    _wrapperCrypto.post = function(message, callback) {
        message.meta.profile = _profile;
        _originalCrypto.post(message, callback);
    };

    _wrapperCrypto.setProfile = function(profile) {
        _profile = profile;
    };

    _wrapperCrypto.debug = function() {
        alert("debug: call wrapper from crypto_wrapper.js");
    };

    _wrapperCrypto.noConflict = function() {
        crypto = _originalCrypto;
        return this;
    };

    _wrapperCrypto.assign = function(object, name) {
        return (window[name] = object);
    };

    _wrapperCrypto.uniqueName = function() {
        return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, c => 
            (c === "x" ? (Math.random() * 16 | 0) : ((Math.random() * 16 | 0) & 0x3 | 0x8)).toString(16)
        );
    };

    _wrapperCrypto.certificates = function(request, callback) {
        const handler = (message) => {
            handle(message, (parsed) => parsed.map(format));
            callback(message);
        };
        return _originalCrypto.certificates(request, handler);
    };

    _wrapperCrypto.certificateFields = function(request, callback) {
        const handler = (message) => {
            handle(message, format);
            callback(message);
        };
        return _originalCrypto.certificateFields(request, handler);
    };

    _wrapperCrypto.signatureV2 = function(request, callback) {
        const handler = (message) => {
            handle(message, (parsed) => {
                if (parsed.certificate) {
                    parsed.certificate = format(parsed.certificate);
                }
                return parsed;
            });
            callback(message);
        };
        return _originalCrypto.signatureV2(request, handler);
    };

    _wrapperCrypto.tokens = function(request, callback) {
        const handler = (message) => {
            handle(message, (parsed) => {
                parsed.forEach(entity => {
                    if (Array.isArray(entity.certificates)) {
                        entity.certificates = entity.certificates.map(format);
                    }
                });
                return parsed;
            });
            callback(message);
        };
        return _originalCrypto.tokens(request, handler);
    };

    crypto = _wrapperCrypto;
};

document.addEventListener("DOMContentLoaded", () => {
    wrap(crypto);
    _wrapperCrypto.setProfile({
        "container": "true",
        "provider": "true",
        "cert_validity": "true",
        "no_certificates": "true",
        "certificate_chain": "true"
    });
});