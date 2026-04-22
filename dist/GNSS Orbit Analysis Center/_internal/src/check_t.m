function tt = check_t(t)

% This function repairs over- and under-flow of GPS time
%
% Input:       t  - time in seconds of week
%              tt - repaired time

half_week = 302400;
tt = t;

if t >  half_week, tt = t-2*half_week; end
if t < -half_week, tt = t+2*half_week; end

