function [sapc] = calc_satapc(spos,sunpos,satx,prn)

% constants
[f1,~] = gnss_freq('G',1,1);
[f2,~] = gnss_freq('G',1,2);
a1 = (f1^2)/(f1^2 - f2^2);
a2 = -(f2^2)/(f1^2 - f2^2);

% satellite-fixed coordinate system
k = (-1).*(spos./(norm(spos)));
rs  = sunpos - spos;
e   = rs./(norm(rs));
j   = cross(k,e)./norm(cross(k,e));
i   = cross(j,k);
%sf  = [i; j; k];
sf = vertcat(i,j,k);

% antenna offsets for first and second frequencies
de1 = (satx.gps.neu(prn,:,1))';
de2 = (satx.gps.neu(prn,:,2))';

deif = a1*de1 + a2*de2;
sapc = (sf\deif)./1000;

end