function [brdc,err] = read_brd(fname)
% This function reads the navigation message in RINEX 3.xx and 2.xx formats
% Input  : fname - the name of navigation file [char][ ]
% Output : brdc  - the structure including header and obsevation parts [structure] 

% get the RINEX version of the related navigation file
[ver] = get_ver(fname);
% read the observation file line-by-line
if ver>=3
    [brdc,err] = read_brdv3(fname);
elseif ver>=2
    [brdc,err] = read_brdv2(fname);
end

end

function [ver] = get_ver(fname)
% This function determines the RINEX version of navigation file
% Input  : fname - the name of navigation file [char][ ]
% Output : ver   - version of the rinex file [num][%4.2f]

% open the file
[fid,errmsg] = fopen(fname);
% read the file line-by-line
if ~any(errmsg)
    while 1
        tline = fgetl(fid);
        tag  = strtrim(tline(61:end));
        % find the version of rinex file
        if strcmp(tag,'RINEX VERSION / TYPE')
            ver = sscanf(tline(1:20),'%f');
            break
        end
    end
end
% close the file
fclose('all');
end