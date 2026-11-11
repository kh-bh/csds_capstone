const ZIP_FILE_URL = "/US.txt";

let zipDataPromise;

export function loadZipData() {
  if (!zipDataPromise) {
    zipDataPromise = fetch(ZIP_FILE_URL)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Could not load ${ZIP_FILE_URL} (HTTP ${res.status})`);
        }

        const text = await res.text();
        if (text.trim().startsWith("<")) {
          throw new Error(
            `${ZIP_FILE_URL} not found - put US.txt in your /public folder`
          );
        }

        const lookup = {};
        text.split(/\r?\n/).forEach((line) => {
          const cols = line.split("\t");
          if (cols.length < 11) return;

          const zip = cols[1].trim().padStart(5, "0");
          const state = cols[4].trim().toUpperCase();
          const lat = parseFloat(cols[9]);
          const lon = parseFloat(cols[10]);
          if (
            /^\d{5}$/.test(zip) &&
            Number.isFinite(lat) &&
            Number.isFinite(lon)
          ) {
            lookup[zip] = { state: state || null, lat, lon };
          }
        });

        return lookup;
      })
      .catch((error) => {
        zipDataPromise = undefined;
        throw error;
      });
  }

  return zipDataPromise;
}
