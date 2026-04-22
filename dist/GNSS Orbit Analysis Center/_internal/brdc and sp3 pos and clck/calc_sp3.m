function [ssp3] = calc_sp3(sp3,satx,prn,tim)

int = sp3.sp3int;

xs = sp3.gps(:,1,prn);
ys = sp3.gps(:,2,prn);
zs = sp3.gps(:,3,prn);
cs = sp3.gps(:,4,prn);

epoch = tim.sec;
[x,~]  = entrp(epoch,int,xs);
[y,~]  = entrp(epoch,int,ys);
[z,~]  = entrp(epoch,int,zs);
[dt,~] = entrp(epoch,int,cs);

spos = [x y z];

% sun position
[sunpos] = calc_sunpos(tim.mjdtt);

[sapc] = calc_satapc(spos,sunpos,satx,prn);

spos = spos + sapc';

ssp3 = horzcat(spos,dt);

end