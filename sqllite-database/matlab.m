f=10; %frequency of sine wave
overSampRate=30; %oversampling rate
fs=overSampRate*f; %sampling frequency
phase = 1/3*pi; %desired phase shift in radians
nCyl = 5; %to generate five cycles of sine wave

t=0:1/fs:nCyl*1/f; %time base

x=sin(2*pi*f*t+phase); %replace with cos if a cosine wave is desired
plot(t,x);
title(['Sine Wave f=', num2str(f), 'Hz']);
xlabel('Time(s)');
ylabel('Amplitude');

figure
NFFT=1024;	 	 
L=length(x);	 	 
X=fftshift(fft(x,NFFT));	 	 
Px=X.*conj(X)/(NFFT*L); %Power of each freq components	 	 
fVals=fs*(-NFFT/2:NFFT/2-1)/NFFT;	 	 
plot(fVals,10*log10(Px),'b');	 	 
title('Power Spectral Density');	 	 
xlabel('Frequency (Hz)')	 	 
ylabel('Power');


figure
L=length(x);	 	 
NFFT=1024;	 	 
X=fft(x,NFFT);	 	 
Px=X.*conj(X)/(NFFT*L); %Power of each freq components	 	 
fVals=fs*(0:NFFT/2-1)/NFFT;	 	 
plot(fVals,Px(1:NFFT/2),'b','LineSmoothing','on','LineWidth',1);	 	 
title('One Sided Power Spectral Density');	 	 
xlabel('Frequency (Hz)')	 	 
ylabel('PSD');