function [sp3] = read_sp3(fname)


sp3.gps = NaN(96,4,32);
sp3.eph = NaN(96,1);
sp3.sp3int = 30;


[fid,~] = fopen(fname);
while ~feof(fid)
    %%
    line = fgetl(fid);
    if strcmp(line(1),'#') && ~strcmp(line(1:2),'##')
        dat = sscanf(line(4:14),'%f');
    end
    if strcmp(line(1:2),'##')
        sp3int = sscanf(line(25:38),'%f');
        sp3.sp3int = sp3int;
        epn = 86400/sp3int; 
        sp3.gps = NaN(epn,4,32);
        sp3.eph = NaN(epn,1);
    end
    
    if line(1)=='+'
        temp = sscanf(line(4:6),'%d');
        if ~isnan(temp)
            nosat = temp;
        end
    end

    %%
    if line(1)=='*'
        ep   = sscanf(line(2:end),'%f',[1,6]);
        if ep(1)==dat(1) && ep(2)==dat(2) && ep(3)==dat(3)
            nep = ((ep(4)*3600 + ep(5)*60 + ep(6))/sp3int) + 1;
            sp3.eph(nep,1) = ep(4)*3600 + ep(5)*60 + ep(6);
            for k=1:nosat
                line = fgetl(fid);
                if strcmp(line(2),'G')
                    sno  = sscanf(line(3:4),'%d');
                    if sno>size(sp3.gps,3)
                        continue
                    else
                        temp = sscanf(line(5:end),'%f',[1,4]);
                        if ~isempty(temp(1:3))
                            sp3.gps(nep,1:3,sno) = temp(1:3)*1000;
                        end
                        if ~isempty(temp(4)) && temp(4)~=999999.999999
                            sp3.gps(nep,  4,sno) = temp(4)*10^-6;
                        end
                    end
                end        
            end
        end
    end
end

fclose('all');

end