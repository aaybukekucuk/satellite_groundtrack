function jd = gps2jd(gpsweek,sow,rollover)

% This function converts GPS week number (since 1980.01.06) and
%  seconds of week to Julian date. 
%
% Input:   gpsweek  - GPS week number
%          sow      - seconds of week since 0 hr, Sun (default=0)
%          rollover - number of GPS week rollovers (default=0)
%
% Output:  jd       - Julian date

if nargin < 1 | nargin >3
  warning('Incorrect number of arguments');
  return;
end
if nargin < 3
  rollover = 0;
end
if nargin < 2
  sow = 0;
end
if gpsweek <= 0
  warning('GPS week must be greater than or equal to zero');
  return;
end

jdgps = cal2jd(1980,1,6);             % beginning of GPS week numbering
nweek = gpsweek + 1024*rollover;      % account for rollovers every 1024 weeks
jd = jdgps + nweek*7 + sow/3600/24;