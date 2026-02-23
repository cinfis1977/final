# Terim-Bazlı Eşleme: Master Denklemi ↔ Repo Runners

Bu not, repo'daki mevcut "phase-kernel" ve "multiplicative modulation" yaklaşımlarının, kaotik/geometrik katkıları içeren yoğunluk-matrisi (master/GKSL) denklemiyle nasıl eşlendiğini ve hangi şartlar altında geçerli bir yaklaşıklama olduklarını kısa ve teknik bir şekilde toplar.

**Ana denklemin formu**

Yoğunluk matrisi $rho(L)$, yayılma uzunluğu $L$ boyunca (kovaryant olmayan tek boyutlu parametreleştirme) şu biçimde evrilir:

$$
\frac{d\rho}{dL} = -i\big[H(L,E),\rho\big] + \mathcal{D}[\rho],
$$

burada $H(L,E)=H_{\rm vac}(E)+H_{\rm mat}(L,E)+\delta H_{\rm geo}(L,E)$ ve $\mathcal{D}[\rho]$ açık sistem (dekoherans/dissipasyon) terimidir.

- $H_{\rm vac}(E)$: vakum Hamiltonyani; tipik olarak $\frac{1}{2E}U\,\mathrm{diag}(m_i^2)\,U^\dagger$ formunda.
- $\delta H_{\rm geo}(L,E)$: geometri/çevre kaynaklı, lokasyon ve enerjiye bağlı ek kütle-kare matrisi (repo'da `deltaM^2_geo` olarak adlandırılan bileşenlere karşılık gelir).
- $\mathcal{D}[\rho]$: Lindblad veya dephasing tarzı operatör; örn. tek-kanal dekoherans için $\gamma(\sigma_z\rho\sigma_z-\rho)$ gibi yapı.


**Repo yaklaşımlarının (runner'ların) eşlemeleri**

- Phase-kernel / phase-shift yaklaşımı (ör: `kernel_phase_dphi_components`, `apply_phase_shift_to_prob`):
  - Varsayım: $\delta H_{\rm geo}(L,E)$, baz dönüşümünde yaklaşık olarak diyagonal ve/veya $[H_{\rm vac},\delta H_{\rm geo}] 0$ olacak kadar küçük değişiklikler üretiyor. Bu durumda ek faz kayması aday olarak

    $$
    d\phi(L,E) \approx \frac{\delta m^2_{\rm eff}(L,E)}{2E}\,dL
    $$

    ile hesaplanabilir; entegre edilip ana faza eklenince doğrudan osilasyon terimine etki eder:

    $$
    \Delta(L,E)\to\Delta(L,E)+\int_0^L d\phi(\ell,E).
    $$

  - Yorum: Runner'lar genellikle $d\phi/dL$ hesaplayıp bunu per-bin (ya da per-baseline) olasılığa uyguluyor; bu, adyabatik ve komütatörün küçük olduğu sınırda doğru bir yaklaşıklamadır.

- Multiplicative modulation (ör: `pred_geo = pred_sm*(1+\delta)`):
  - Varsayım: Geometrik etkiler olasılık düzeyinde küçük, lineer yanıt geçerli. Bu, ya yoğunluk-matrisindeki dışsal damping/inelastic kayıpların (ölçümsel verim kaybı vb.) etkisi olarak modellenebilir — yani, $\mathcal{D}[\rho]$ net bir oranla koherent amplitüdleri azaltır ve sonuçta gözlenen olasılık ölçeklenir.
  - Yorum: Bu yaklaşım, $\delta P/P\ll 1$ ve koherensin büyük oranda korunmadığı (ya da tekniğe göre ortalama alındığı) durumlarda makul olabilir; ancak komütatif olmayan Hamiltonyan etkileri göz ardı eder.

- `env_scale` veya benzeri skaler çarpanlar:
  - Bu skalerler pratikte iki farklı fiziksel yoruma karşılık gelebilir: (i) $\delta H_{\rm geo}\propto$ `env_scale` (yani kütle-kare katkısının genliği), veya (ii) Lindblad hızlarının/kuplajlarının skalanması (yani $\mathcal{D}[\rho]\propto$ `env_scale`). Runnner'larda hangi yorum kullanıldığı kod okunarak belirlenmelidir — ikisi farklı fiziksel sonuçlar verir.


**Geçerlilik şartları / kırılmalar**

- Adyabatiklik: Eğer $\delta H_{\rm geo}(L,E)$ yavaş değişiyorsa ve ana Hamiltonyanın eigenbasis'i boyunca hareket ediyorsa, faz-integrasyonu (phase-kernel) geçerli olabilir.
- Komütatör smallness: $[H_{\rm vac}+H_{\rm mat},\,\delta H_{\rm geo}]\ll$ tipik enerji ölçeği. Aksi halde faz etkisi, transfer ve yeniden karışma ile birlikte çalışır; basit faz kaydırması yetersizdir.
- Zayıf açık-sistem limit: Eğer $\mathcal{D}[\rho]$ çok küçük ise koherent evrim hakimdir; büyük $\mathcal{D}$ durumunda osilasyonlar sönümlenir ve multiplicative bir çarpan daha mantıklıdır.
- Lineer cevap: `pred_geo = pred_sm*(1+\delta)` sadece küçük değişiklikler için dayanıklıdır; daha büyük etkilerde olasılıkların yeniden normalizasyonu, negatif değerler ve CPTP (completely-positive trace-preserving) bozulmaları kontrol edilmelidir.


**Kesin testler / doğrulama adımları (öneriler)**

1. Referans hesap: Basit 2-flavor GKSL/Open-system entegresyonu (repo'ya eklenen `mastereq/gk_sl_solver.py`) kullanılarak tam yoğunluk-matrisi evrimi hesaplanmalı.
2. Phase-approx doğrulaması: Aynı başlangıç koşulları ve $\delta H_{\rm geo}$ fonksiyonu için
   - $P_{\rm GKSL}(L,E)$ ve $P_{\rm phase}(L,E)$ karşılaştırılmalı,
   - Hata eşiği verilmeli; örn. $|P_{\rm GKSL}-P_{\rm phase}|<\epsilon$ için koşullar (A, gamma, dphi büyüklüğü) raporlanmalı.
3. CPTP kontrolü: Runner'ların ürettiği `pred_geo` sonuçları fiziksel olasılıklar (0..1) ve toplam iz korunumu (varsa) açısından kontrol edilmeli.
4. İyi-pratik: Hızlı ızgara taraması (`out/gksl_grid.csv`) ile parametre uzayı taranmalı ve yanlışlık/sapma tabloları oluşturulmalı.


**Kısa sonuç / tavsiye**

- Repo'daki mevcut phase-kernel uygulamaları, adyabatik ve zayıf komütatör koşulları altında master-denkleme karşı mantıklı bir yaklaşıklamadır; fakat bu koşullar çoğu pratik durumda açıkça doğrulanmalıdır.
- Eğer hedef kesinlik yüksekse (özellikle kuantum koherensi/rekombinasyon etkilerinin kritik olduğu bölgelerde), full GKSL entegrasyonu önerilir ve mevcut runner'lar referans olarak bu şekilde doğrulanmalıdır.


Referans: Bu not, repo içindeki `nova_mastereq_forward_kernel_BREATH_THREAD_*.py` ve `em_*_forward*.py` gibi runner'ların kodundan çıkarılan kullanım desenlerine dayanır; daha ayrıntılı eşlemeler hat/kalıp düzeyinde eklenebilir.

## Açık, denklemsel eşlemeler ve kod referansları

Aşağıda master-denklemin (GKSL/Lindblad) terimleri ile repo içindeki en önemli fonksiyonlar/parametreler arasındaki doğrudan matematiksel eşlemeler verilmektedir. Bunlar, yapılan numerik uygulamaları kesin biçimde birbirine bağlamak için kullanılabilir.

- Master denklemi (tekrar hatırlatma):

  $$
  \frac{d\rho}{dL} = -i\big[H(L,E),\rho\big] + \mathcal{D}[\rho].
  $$

- Hamiltonyan bileşeni açıklaması:

  $$
  H(L,E) = H_{\rm vac}(E) + H_{\rm mat}(L,E) + \delta H_{\rm geo}(L,E).
  $$

  Burada (iki-flavor toy için) kodda kullanılan dönüşüm açıkça:

  - `mastereq/gk_sl_solver.py::vacuum_hamiltonian_2flavor(dm2,theta,E)`:
    inşa eder
    $$H_{\rm vac} = K\cdot\frac{1}{2E}\,U\,\mathrm{diag}(0,\,\Delta m^2)\,U^\dagger$$
    K = 1.267 \quad\text{(kodda `KCONST`)},

  - `mastereq/gk_sl_solver.py::geometric_delta_m2_2flavor(base_dphi_dL, E, scale)` fonksiyonu bir kütle-kare matrisine karşılık gelen bir skaler/projeksiyon döndürür; `build_Hfn_2flavor` içinde bu matris şöyle kullanılır:

    $$
    \delta H_{\rm geo}(L,E) = K\cdot U\left(\frac{\delta M^2_{\rm mass}(L,E)}{2E}\right)U^\dagger,
    $$

    yani kodda önce `deltaM2_mass` üretilir, sonra `/ (2E)` ile bölünür ve `KCONST` ile faz birimine çevrilir.

  - Kod bağlantısı: `mastereq/gk_sl_solver.py::build_Hfn_2flavor`.

- Phase-kernel ↔ δM^2/ faz ilişkisi (runner-side):

  - Runner dosyalarında hesaplanan "kernel" genellikle bir baz fonksiyon verir: $k(L,E)\equiv d\phi/dL$ veya yakın benzeri. Hash olarak kodlarda `kernel_phase_dphi_components` vb. adlandırmaları gözlenir.

  - Eşleme (yaklaşım):

    $$
    \frac{d\phi}{dL}(L,E) \approx \frac{\delta m^2_{\rm eff}(L,E)}{2E},
    $$

    ve bu entegre edilirse

    $$
    \phi_{\rm geo}(L,E) = \int_0^L d\ell\,\frac{\delta m^2_{\rm eff}(\ell,E)}{2E}.
    $$

    Runner uygulaması (ör. `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py`) tipik olarak `dphi/dL` hesaplayıp sayısal entegrasyon (`trapz`) ile `int_dphi` üretir ve bunu klasik faz `\Delta`'ya ekler:

    ```text
    Delta_eff = Delta_vac + int_dphi
    P_phase = P_sm(Delta_eff)
    ```

    Buradaki kritik koşul: yukarıdaki dönüşümün doğruluğu için $\delta H_{\rm geo}$'nun vakum Hamiltonyaniyle komütatif etkisi ihmal edilebilmeli ya da adyabatik yaklaşımlar geçerli olmalıdır.

- Lindblad/decoherence teriminin kod eşlemi:

  - Genel Lindblad formu:

    $$
    \mathcal{D}[\rho] = \sum_k \gamma_k\left(L_k\rho L_k^\dagger - \tfrac{1}{2}\{L_k^\dagger L_k,\rho\}\right).
    $$

  - Repo toy-uygulaması (ve bizim solver) için basit off-diagonal dephasing şu şekilde yakalanır (kod: `lindblad_dephasing`):

    $$
    (\mathcal{D}[\rho])_{ij} = -\Gamma_{ij}(L,E)\,\rho_{ij},\quad i\neq j,
    $$

    yani popülasyonlar korunur, koheranslar sönümlenir. Kod yapılandırması: `mastereq/gk_sl_solver.py::build_Dfn_simple` okunarak `gamma0 * junction_scale(L,E)` ile ilişkilendirilir.

- `pred_geo = pred_sm*(1+\delta)` eşlemi:

  - Bu, gözlemsel seviyede küçük-nicelik yaklaşımıdır. Matematiksel olarak

    $$
    P_{\rm geo}(E,L) \approx P_{\rm sm}(E,L)\big(1 + \delta(E,L)\big),\qquad |\delta|\ll 1.
    $$

  - Burada `\delta` kodda genellikle `env_scale * f(kernel)` gibi bir yapıdan türetilir; örn. `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py` içinde `pred_geo = pred_sm * (1+delta)` satırı doğrudan bu eşlemeyi gerçekleştirmektedir.


## Kısa kontrol listesi — hangi kod-parçaları hangi terime karşılık gelir

- `mastereq/gk_sl_solver.py`:
  - `vacuum_hamiltonian_2flavor` → $H_{\rm vac}$ (KCONST dönüşümü dahil)
  - `geometric_delta_m2_2flavor` → üretici fonksiyon: `deltaM2_mass(L,E)` (koda göre mass-basis)
  - `build_Hfn_2flavor` → $H_{\rm vac} + \delta H_{\rm geo}$ dönüşümü (U dönüşümü ve `/2E`, `KCONST` uygulanır)
  - `build_Dfn_simple`, `lindblad_dephasing` → $\mathcal{D}[\rho]$ (basit off-diag dephasing)

- Runners:
  - `nova_mastereq_forward_kernel_BREATH_THREAD_fixedbyclaude.py` / `*_v2.py`:
    - `kernel_phase_dphi_components` → hesaplanan `dphi/dL` bileşenleri (kod içinde `dphi`), `apply_phase_shift_to_prob` → entegre fazı olasılığa uygular.
  - `em_bhabha_forward_shapeonly_env_guarded_freezebetas_groupaware.py`, `em_mumu_forward.py`:
    - `pred_geo = pred_sm * (1 + delta)` → multiplicative modulation; `delta` skalerinin kaynağı `env_scale` ve kernel özetleri olabilir.


## Pratik dönüşümler (özet)

- Eğer elinizde runner'ın ürettiği `dphi/dL` (kodda `base_dphi_dL`) varsa, GKSL tarafına geçirmek için:

  1. `deltaM2_mass(L,E) \leftarrow scale\times base_dphi_dL(L,E)` (kodumuzda `geometric_delta_m2_2flavor` ile yapılır).
  2. `\delta H_{\rm geo}(L,E) = K * U [\delta M^2_{\rm mass}/(2E)] U^\dagger` (kodda `build_Hfn_2flavor`).
  3. `\mathcal{D}[\rho]` için kernel/`env_scale` kullanılacaksa `gamma(L,E)=gamma0*env_scale(L,E)` şeklinde parametreleştirilip `build_Dfn_simple` ile verilir.


Bu eklemelerle birlikte `term_by_term_mapping.md` dosyası artık hem kavramsal notları hem de doğrudan kod+denklem eşlemlerini içeriyor; bu sayede yapılan kod değişiklikleri ve hesaplar boşa gitmez, tersine runner implementasyonlarının hangi varsayımlarla master-denkleme karşılık geldiği açıkça izlenebilir.
