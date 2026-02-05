export const downloadEFIR = async (touristId) => {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/generate-efir/${touristId}`, {
            headers: {
                'X-Justification': 'Immediate Incident Export',
                'X-Role': 'DISTRICT_SUPERVISOR',
                'X-Actor-ID': 'officer-web-01'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const blob = await response.blob();

        // Create a temporary link to trigger the browser download
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `EFIR_${touristId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
    } catch (error) {
        console.error("Download failed", error);
        alert("Could not generate E-FIR. Check backend connectivity.");
    }
};
