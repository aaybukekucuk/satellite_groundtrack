function [week,sec_of_week] = gps_time(julday)

% This function converts Julian Day number to GPS week and seconds of Week reckoned from Saturday midnight
% 
% Input :       julday      - Julian Day number
%
% Output:       week        - GPS week
%               sec_of_week - seconds of Week reckoned from Saturday midnight

a = floor(julday+.5);
b = a+1537;
c = floor((b-122.1)/365.25);
e = floor(365.25*c);
f = floor((b-e)/30.6001);
d = b-e-floor(30.6001*f)+rem(julday+.5,1);
day_of_week = rem(floor(julday+.5),7);
week = floor((julday-2444244.5)/7);
% We add +1 as the GPS week starts at Saturday midnight
sec_of_week = (rem(d,1)+day_of_week+1)*86400;

week = week + floor(sec_of_week/(86400*7));
sec_of_week = mod(sec_of_week,86400*7);
sec_of_week = round(sec_of_week*10)/10; % frz: to avoid eventual numerical problems sec_of_week is rounded to a tenth of seconds
