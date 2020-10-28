%% CT Classification by Estimation-Maximization Algorithm
clear; clc;

%% open a CT nifti file
rawimage = niftiread('yejiguoCT.nii.gz'); % Here, type in the test data filename.
[row, col, slice] = size(rawimage);
X = reshape(rawimage, [], 1);
X = single(X);
X = normalize(X, 'range');

%% initialize parameters
N = size(X, 1);
n1 = N / 4; % we pre-set 4 types of CT voxels (electrodes, skull, matter & the rest)
n2 = N / 4;
n3 = N / 4;
n4 = N / 4;
p_z1 = 1 / 4; % prior i.e. P(zx)
p_z2 = 1 / 4;
p_z3 = 1 / 4;
p_z4 = 1 / 4;
% mean value of each type of voxels，set initially
u_1 = 0.15; % the rest mean
u_2 = 0.4; % matter(gray/white) mean
u_3 = 0.65; % skull mean
u_4 = 0.9; % electrodes mean
% variance value of each type of voxels, set initially
sigma_1 = sum((X - mean(X)).^2) / N;
sigma_2 = sigma_1;
sigma_3 = sigma_1;
sigma_4 = sigma_1;

%% 1st Estimation-step
% likelihoods i.e. P(x|zx)
p_x_z1 = normpdf(X, u_1, sqrt(sigma_1));
p_x_z2 = normpdf(X, u_2, sqrt(sigma_2));
p_x_z3 = normpdf(X, u_3, sqrt(sigma_3));
p_x_z4 = normpdf(X, u_4, sqrt(sigma_4));
% marginal i.e. P(x)
p_x = p_x_z1*p_z1 + p_x_z2*p_z2 + p_x_z3*p_z3 + p_x_z4*p_z4;
J = sum(log(p_x));
% posteriors & soft classifier i.e. P(zx|x)
p_z1_x = p_x_z1*p_z1 ./ p_x;
p_z2_x = p_x_z2*p_z2 ./ p_x;
p_z3_x = p_x_z3*p_z3 ./ p_x;
p_z4_x = p_x_z4*p_z4 ./ p_x;
p_z_x = [p_z1_x, p_z2_x, p_z3_x, p_z4_x];

for i = 1:40
    % Maximization-step
    % labelling each voxels
    [M, ind] = max(p_z_x, [], 2);
    % number of data points in each class
    n1 = size(find(ind==1), 1);
    n2 = size(find(ind==2), 1);
    n3 = size(find(ind==3), 1);
    n4 = size(find(ind==4), 1);
    % index of data points in each class
    ind_1 = find(ind==1);
    ind_2 = find(ind==2);
    ind_3 = find(ind==3);
    ind_4 = find(ind==4);
    % mixing proportions / priors
    p_z1 = n1/N;
    p_z2 = n2/N;
    p_z3 = n3/N;
    p_z4 = n4/N;
    % estimations of means & variances
    u_1 = mean(X(ind_1));
    u_2 = mean(X(ind_2));
    u_3 = mean(X(ind_3));
    u_4 = mean(X(ind_4));
    sigma_1 = sum((X(ind_1)-u_1).^2) / n1;
    sigma_2 = sum((X(ind_2)-u_2).^2) / n2;
    sigma_3 = sum((X(ind_3)-u_3).^2) / n3;
    sigma_4 = sum((X(ind_4)-u_4).^2) / n4;
    % Estimation-step
    % likelihoods
    p_x_z1 = normpdf(X, u_1, sqrt(sigma_1));
    p_x_z2 = normpdf(X, u_2, sqrt(sigma_2));
    p_x_z3 = normpdf(X, u_3, sqrt(sigma_3));
    p_x_z4 = normpdf(X, u_4, sqrt(sigma_4));
    % marginal
    p_x = p_x_z1 * p_z1 + p_x_z2 * p_z2 + p_x_z3 * p_z3 + p_x_z4 * p_z4;
    J = [J, sum(log(p_x))];
    % posteriors & soft classifier
    p_z1_x = p_x_z1 * p_z1 ./ p_x;
    p_z2_x = p_x_z2 * p_z2 ./ p_x;
    p_z3_x = p_x_z3 * p_z3 ./ p_x;
    p_z4_x = p_x_z4 * p_z4 ./ p_x;
    p_z_x = [p_z1_x, p_z2_x, p_z3_x, p_z4_x];
end

%% Loss function
figure % curve of loss function, should be convergent if trained well
plot(1:1:41, J)
title('Log-likelihood')
xlabel('iterations')
ylabel('J')

[B, I] = sort([u_1, u_2, u_3, u_4]);
X_1 = ones(N, 4);
X_1(ind_1, 1) = 0;
X_1(ind_2, 2) = 0;
X_1(ind_3, 3) = 0;
X_1(ind_4, 4) = 0;

% figure
image_out = reshape(X_1(:, I(1)), row, col, slice);
image_matter = reshape(X_1(:, I(2)), row, col, slice);
image_skull = reshape(X_1(:, I(3)), row, col, slice);
image_elec = reshape(X_1(:, I(4)), row, col, slice);

%% slice imaging
middle_slice = fix(slice / 2);

figure
imshow(image_out(:,:,middle_slice))

figure
imshow(image_matter(:,:,middle_slice))

figure
imshow(image_skull(:,:,middle_slice))

figure
imshow(image_elec(:,:,middle_slice))

%% electrode positions in 3-D
k1 = find(~image_elec);
k1_slice = fix((k1-1)/(row*col))+1;
k1_col = fix(rem((k1-1),(row*col))/row)+1;
k1_row = rem(rem((k1-1),row*col),row)+1;

figure
scatter3(k1_row, k1_col, k1_slice, '.')
title('3D electrode positions')