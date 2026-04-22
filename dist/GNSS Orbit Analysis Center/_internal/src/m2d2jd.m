function jd = mjd2jd(mjd)

%   This function converts Modified Julian Date to Julian Date.

if nargin ~= 1
  warning('Incorrect number of arguments');
  return;
end

jd=mjd+2400000.5;