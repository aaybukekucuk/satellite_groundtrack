function mjd=jd2mjd(jd)

% This function converts Julian Date to Modified Julian Date.

if nargin ~= 1
  warning('Incorrect number of arguments');
  return;
end

mjd=jd-2400000.5;