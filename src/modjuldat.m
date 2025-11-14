function tmjd = modjuldat(y,m,d,h,mi,s)

% This function converts date to modified julian date
%
% input 
% y  : years, e.g. 2007 (n x 1 vector)
% m  : months (n x 1 vector)
% d  : days (n x 1 vector)
% h  : hours (n x 1 vector)
% mi : minutes (n x 1 vector)
% s  : seconds (n x 1 vector)
%
% output 
% tmjd  : modified Julian dates (n x 1 vector)

n_mjd = size(y, 1);

if (nargin < 6)
    s = zeros(n_mjd, 1);
    if (nargin < 5)
        mi = zeros(n_mjd, 1);
        if (nargin < 4)
            h = zeros(n_mjd, 1);
            if (nargin < 3)
                d = ones(n_mjd, 1);
                if (nargin < 2)
                    m = ones(n_mjd, 1);
                end
            end
        end
    end
end

ind = m <= 2;
m(ind) = m(ind) + 12;
y(ind) = y(ind) - 1;

% if date is before Oct 4, 1582
b = zeros(n_mjd, 1);
ind = (y <= 1582) & (m <= 10) & (d <= 4);
b(ind)  = -2;
% if date is after Oct 4, 1582
b(~ind) = floor(y(~ind)/400)-floor(y(~ind)/100);

jd      = floor(365.25.*y)-2400000.5;
tmjd    = jd + floor(30.6001.*(m+1)) + b + 1720996.5 + d + h./24 + mi./1440 + s./86400;