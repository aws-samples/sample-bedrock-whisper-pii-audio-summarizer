function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Set proper CORS headers
    headers['access-control-allow-origin'] = {value: 'https://dfkwm5303lopi.cloudfront.net'};
    headers['access-control-allow-methods'] = {value: 'GET,POST,OPTIONS,PUT,DELETE'};
    headers['access-control-allow-headers'] = {value: 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'};
    headers['access-control-allow-credentials'] = {value: 'true'};
    headers['access-control-max-age'] = {value: '86400'};

    return response;
}
