import ee

class KGCC:

  @staticmethod
  def classify(p_ic=None, t_ic=None, hemi=None):
    """
    Produces a classified image with value ranges of 1 to 30.

    Parameters
    ----------
    p_ic : ee.ImageCollection
           12 monthly precipitation images (Units of mm).
    t_ic : ee.ImageCollection
           12 monthly mean temperature images (Units of Celsius).
    hemi : string
           Should be "north" or "south" for the hemisphere of the map coverage.

    Returns
    -------
    type_im : ee.Image
              Classified image loaded to memory.

    Notes
    -----
    - Assumes WGS84 coordinate system.
    - Assumes overlapping input images that exist only within selected hemisphere.
    """
    ndays_months = ee.List([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    if hemi == 'north':
      summr_months = ee.List([4, 5, 6, 7, 8, 9])
      wintr_months = ee.List([1, 2, 3, 10, 11, 12])
    elif hemi == 'south':
      wintr_months = ee.List([4, 5, 6, 7, 8, 9])
      summr_months = ee.List([1, 2, 3, 10, 11, 12])
    else:
      pass

    t_ic_list = t_ic.toList(12)
    def month_wt_fn(idxobj):
      m_idx = ee.Number(idxobj)
      month_im = ee.Image(t_ic_list.get(m_idx))
      weight_im = month_im.multiply(ee.Number(ndays_months.get(m_idx))).divide(365.25)
      return weight_im
    wt_ic = ee.ImageCollection(ee.List.sequence(0, 11).map(month_wt_fn))
  
    tann_im = wt_ic.reduce(ee.Reducer.sum())
    pann_im = p_ic.reduce(ee.Reducer.sum())
    tw_im = t_ic.reduce(ee.Reducer.max())
    tc_im = t_ic.reduce(ee.Reducer.min())
    pd_im = p_ic.reduce(ee.Reducer.min())
  
    #Binary test images, etc.
    zero_im = pann_im.lt(0.0)
    def make_p_seasn_fn(month):
      month = ee.Number(month)
      mo_im = ee.Image(p_ic.toList(12).get(month.subtract(1)))
      return mo_im
  
    pwintr_ic = ee.ImageCollection(wintr_months.map(make_p_seasn_fn))
    psummr_ic = ee.ImageCollection(summr_months.map(make_p_seasn_fn))
    pwintr_im = pwintr_ic.reduce(ee.Reducer.sum())
    psummr_im = psummr_ic.reduce(ee.Reducer.sum())
    pwintrw_im = pwintr_ic.reduce(ee.Reducer.max())
    pwintrd_im = pwintr_ic.reduce(ee.Reducer.min())
    psummrw_im = psummr_ic.reduce(ee.Reducer.max())
    psummrd_im = psummr_ic.reduce(ee.Reducer.min())
    pd_in_summr_im = psummrd_im.lt(pwintrd_im)
    pd_in_wintr_im = pwintrd_im.lt(psummrd_im)
  
    test_im = ee.Image(pann_im.multiply(0.70))
    conA_im = pwintr_im.gte(test_im)
    conB_im = psummr_im.gte(test_im)
    conAB_im = conA_im.add(conB_im)
    conC_im = conAB_im.eq(0.0)
  
    pthrA_im = conA_im.where(conA_im, tann_im.multiply(2.0))
    pthrB_im = conB_im.where(conB_im, ee.Image(tann_im.multiply(2.0)).add(28.0))
    pthrC_im = conC_im.where(conC_im, ee.Image(tann_im.multiply(2.0)).add(14.0))
    pthr_im = pthrA_im.add(pthrB_im).add(pthrC_im)
  
    dry_summrA_im = zero_im.where(psummrd_im.lt(pwintrd_im), 1)
    dry_summrB_im = zero_im.where(pwintrw_im.gt(psummrd_im.multiply(3.0)), 1)
    dry_summrC_im = zero_im.where(psummrd_im.lt(40.0), 1)
    mix_im = dry_summrA_im.add(dry_summrB_im).add(dry_summrC_im)
    dry_summr_im = mix_im.eq(3.0)
  
    dry_wintrA_im = zero_im.where(pwintrd_im.lte(psummrd_im), 1)
    dry_wintrB_im = zero_im.where(psummrw_im.gt(pwintrd_im.multiply(10.0)), 1)
    mix_im = dry_wintrA_im.add(dry_wintrB_im)
    dry_wintr_im = mix_im.eq(2.0)
  
    hot_summr_im = zero_im.where(tw_im.gte(22.0), 1)
    sin_hot_summr_im = hot_summr_im.eq(0)
  
    def count_warm_months_fn(t_im):
      warm_im = ee.Image(t_im.gte(10.0))
      return warm_im
  
    warm_ic = ee.ImageCollection(t_ic.map(count_warm_months_fn))
    warm_mo_ct_im = warm_ic.reduce(ee.Reducer.sum())
    warm_mo_im = warm_mo_ct_im.gte(4)
  
  
  
    #E
    e_im = tw_im.lte(10.0)
  
    #Et
    con_et_im = tw_im.gt(0.0)
    mix_im = e_im.add(con_et_im)
    et_im = mix_im.eq(2.0)
  
    #Ef
    con_ef_im = tw_im.lte(0.0)
    mix_im = e_im.add(con_ef_im)
    ef_im = mix_im.eq(2.0)
  
    #B
    sin_e_im = tw_im.gt(10.0)
    con_b_im = zero_im.where(pann_im.lt(pthr_im.multiply(10.0)), 1)
    mix_im = con_b_im.add(sin_e_im)
    b_im = mix_im.eq(2.0)
    con_bs_im = zero_im.where(pann_im.gte(pthr_im.multiply(5.0)), 1)
    mix_im = b_im.add(con_bs_im)
    bs_im = mix_im.eq(2.0)
    con_bw_im = zero_im.where(pann_im.lt(pthr_im.multiply(5.0)), 1)
    mix_im = b_im.add(con_bw_im)
    bw_im = mix_im.eq(2.0)
  
    #Bsh
    con_bsh_im = zero_im.where(tann_im.gte(18.0), 1)
    mix_im = bs_im.add(con_bsh_im)
    bsh_im = mix_im.eq(2.0)
  
    #Bsk
    con_bsk_im = zero_im.where(tann_im.lt(18.0), 1)
    mix_im = bs_im.add(con_bsk_im)
    bsk_im = mix_im.eq(2.0)
  
    #Bwh
    con_bwh_im = zero_im.where(tann_im.gte(18.0), 1)
    mix_im = bw_im.add(con_bwh_im)
    bwh_im = mix_im.eq(2.0)
  
    #Bwk
    con_bwk_im = zero_im.where(tann_im.lt(18.0), 1)
    mix_im = bw_im.add(con_bwk_im)
    bwk_im = mix_im.eq(2.0)
  
    #D
    mix_im = e_im.add(b_im)
    sin_e_b_im = mix_im.eq(0.0)
    con_d_im = zero_im.where(tc_im.lte(0.0), 1)
    mix_im = sin_e_b_im.add(con_d_im)
    d_im = mix_im.eq(2.0)
    mix_im = d_im.add(dry_summr_im)
    ds_im = mix_im.eq(2.0)
    mix_im = d_im.add(dry_wintr_im)
    dw_im = mix_im.eq(2.0)
    mix_im = d_im.add(ds_im).add(dw_im)
    df_im = mix_im.eq(1.0)
  
    #Dsa
    con_dsa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = ds_im.add(con_dsa)
    dsa_im = mix_im.eq(2.0)
  
    #Dsb
    sin_dsa = dsa_im.eq(0.0)
    mix_im = sin_dsa.add(ds_im).add(warm_mo_im)
    dsb_im = mix_im.eq(3.0)
  
    #Dsc
    sin_dsa = dsa_im.eq(0.0)
    sin_dsb = dsb_im.eq(0.0)
    mix_im = sin_dsa.add(sin_dsb).add(ds_im)
    sin_dsa_dsb_im = mix_im.eq(3.0)
    con_dsc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_dsc_im.add(sin_dsa_dsb_im)
    dsc_im = mix_im.eq(2.0)
  
    #Dsd
    sin_dsa = dsa_im.eq(0.0)
    sin_dsb = dsb_im.eq(0.0)
    mix_im = sin_dsa.add(sin_dsb).add(ds_im)
    sin_dsa_dsb_im = mix_im.eq(3.0)
    con_dsd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_dsd_im.add(sin_dsa_dsb_im)
    dsd_im = mix_im.eq(2.0)
  
    #Dwa
    con_dwa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = dw_im.add(con_dwa)
    dwa_im = mix_im.eq(2.0)
  
    #Dwb
    sin_dwa = dwa_im.eq(0.0)
    mix_im = sin_dwa.add(dw_im).add(warm_mo_im)
    dwb_im = mix_im.eq(3.0)
  
    #Dwc
    sin_dwa = dwa_im.eq(0.0)
    sin_dwb = dwb_im.eq(0.0)
    mix_im = sin_dwa.add(sin_dwb).add(dw_im)
    sin_dwa_dwb_im = mix_im.eq(3.0)
    con_dwc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_dwc_im.add(sin_dwa_dwb_im)
    dwc_im = mix_im.eq(2.0)
  
    #Dwd
    sin_dwa = dwa_im.eq(0.0)
    sin_dwb = dwb_im.eq(0.0)
    mix_im = sin_dwa.add(sin_dwb).add(dw_im)
    sin_dwa_dwb_im = mix_im.eq(3.0)
    con_dwd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_dwd_im.add(sin_dwa_dwb_im)
    dwd_im = mix_im.eq(2.0)
  
    #Dfa
    con_dfa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = df_im.add(con_dfa)
    dfa_im = mix_im.eq(2.0)
  
    #Dfb
    sin_dfa = dfa_im.eq(0.0)
    mix_im = sin_dfa.add(df_im).add(warm_mo_im)
    dfb_im = mix_im.eq(3.0)
  
    #Dfc
    sin_dfa = dfa_im.eq(0.0)
    sin_dfb = dfb_im.eq(0.0)
    mix_im = sin_dfa.add(sin_dfb).add(df_im)
    sin_dfa_dfb_im = mix_im.eq(3.0)
    con_dfc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_dfc_im.add(sin_dfa_dfb_im)
    dfc_im = mix_im.eq(2.0)
  
    #Dfd
    sin_dfa = dfa_im.eq(0.0)
    sin_dfb = dfb_im.eq(0.0)
    mix_im = sin_dfa.add(sin_dfb).add(df_im)
    sin_dfa_dfb_im = mix_im.eq(3.0)
    con_dfd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_dfd_im.add(sin_dfa_dfb_im)
    dfd_im = mix_im.eq(2.0)
  
    #C
    mix_im = e_im.add(b_im).add(d_im)
    sin_e_b_d_im = mix_im.eq(0.0)
    con_c_im = zero_im.where(tc_im.lt(18.0), 1)
    mix_im = sin_e_b_d_im.add(con_c_im)
    c_im = mix_im.eq(2.0)
    mix_im = c_im.add(dry_summr_im)
    cs_im = mix_im.eq(2.0)
    mix_im = c_im.add(dry_wintr_im)
    cw_im = mix_im.eq(2.0)
    mix_im = c_im.add(cs_im).add(cw_im)
    cf_im = mix_im.eq(1.0)
  
    #Csa
    con_csa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = cs_im.add(con_csa)
    csa_im = mix_im.eq(2.0)
  
    #Csb
    sin_csa = csa_im.eq(0.0)
    mix_im = sin_csa.add(cs_im).add(warm_mo_im)
    csb_im = mix_im.eq(3.0)
  
    #Csc
    sin_csa = csa_im.eq(0.0)
    sin_csb = csb_im.eq(0.0)
    mix_im = sin_csa.add(sin_csb).add(cs_im)
    sin_csa_csb_im = mix_im.eq(3.0)
    con_csc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_csc_im.add(sin_csa_csb_im)
    csc_im = mix_im.eq(2.0)
  
    #Csd
    sin_csa = csa_im.eq(0.0)
    sin_csb = csb_im.eq(0.0)
    mix_im = sin_csa.add(sin_csb).add(cs_im)
    sin_csa_csb_im = mix_im.eq(3.0)
    con_csd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_csd_im.add(sin_csa_csb_im)
    csd_im = mix_im.eq(2.0)
  
    #Cwa
    con_cwa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = cw_im.add(con_cwa)
    cwa_im = mix_im.eq(2.0)
  
    #Cwb
    sin_cwa = cwa_im.eq(0.0)
    mix_im = sin_cwa.add(cw_im).add(warm_mo_im)
    cwb_im = mix_im.eq(3.0)
  
    #Cwc
    sin_cwa = cwa_im.eq(0.0)
    sin_cwb = cwb_im.eq(0.0)
    mix_im = sin_cwa.add(sin_cwb).add(cw_im)
    sin_cwa_cwb_im = mix_im.eq(3.0)
    con_cwc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_cwc_im.add(sin_cwa_cwb_im)
    cwc_im = mix_im.eq(2.0)
  
    #Cwd
    sin_cwa = cwa_im.eq(0.0)
    sin_cwb = cwb_im.eq(0.0)
    mix_im = sin_cwa.add(sin_cwb).add(cw_im)
    sin_cwa_cwb_im = mix_im.eq(3.0)
    con_cwd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_cwd_im.add(sin_cwa_cwb_im)
    cwd_im = mix_im.eq(2.0)
  
    #Cfa
    con_cfa = zero_im.where(tw_im.gte(22.0), 1)
    mix_im = cf_im.add(con_cfa)
    cfa_im = mix_im.eq(2.0)
  
    #Cfb
    sin_cfa = cfa_im.eq(0.0)
    mix_im = sin_cfa.add(cf_im).add(warm_mo_im)
    cfb_im = mix_im.eq(3.0)
  
    #Cfc
    sin_cfa = cfa_im.eq(0.0)
    sin_cfb = cfb_im.eq(0.0)
    mix_im = sin_cfa.add(sin_cfb).add(cf_im)
    sin_cfa_cfb_im = mix_im.eq(3.0)
    con_cfc_im = zero_im.where(tc_im.gte(-38.0), 1)
    mix_im = con_cfc_im.add(sin_cfa_cfb_im)
    cfc_im = mix_im.eq(2.0)
  
    #Cfd
    sin_cfa = cfa_im.eq(0.0)
    sin_cfb = cfb_im.eq(0.0)
    mix_im = sin_cfa.add(sin_cfb).add(cf_im)
    sin_cfa_cfb_im = mix_im.eq(3.0)
    con_cfd_im = zero_im.where(tc_im.lt(-38.0), 1)
    mix_im = con_cfd_im.add(sin_cfa_cfb_im)
    cfd_im = mix_im.eq(2.0)
  
    #A
    sin_b_im = b_im.eq(0.0)
    con_a_im = zero_im.where(tc_im.gte(18.0), 1)
    mix_im = con_a_im.add(sin_b_im)
    a_im = mix_im.eq(2.0)
  
    #Af
    con_af_im = zero_im.where(pd_im.gte(60.0), 1)
    mix_im = con_af_im.add(a_im)
    af_im = mix_im.eq(2.0)
  
    #Am
    sin_af_im = af_im.eq(0.0)
    hundred_im = zero_im.where(pann_im.gte(0.0), 100.0)
    con_am_im = zero_im.where(pd_im.gte(hundred_im.subtract(pann_im.divide(25.0))), 1)
    mix_im = con_am_im.add(sin_af_im).add(a_im)
    am_im = mix_im.eq(3.0)
  
    #Aw
    sin_af_im = af_im.eq(0.0)
    hundred_im = zero_im.where(pann_im.gte(0.0), 100.0)
    con_aw_im = zero_im.where(pd_im.lt(hundred_im.subtract(pann_im.divide(25.0))), 1)
    mix_im = con_aw_im.add(sin_af_im).add(a_im)
    aw_im = mix_im.eq(3.0)
  
  
  
    #Type value assignments
    af_im = af_im.where(af_im.eq(1.0), 1)
    am_im = am_im.where(am_im.eq(1.0), 2)
    #As not present
    aw_im = aw_im.where(aw_im.eq(1.0), 3)
  
    bwh_im = bwh_im.where(bwh_im.eq(1.0), 4)
    bwk_im = bwk_im.where(bwk_im.eq(1.0), 5)
    bsh_im = bsh_im.where(bsh_im.eq(1.0), 6)
    bsk_im = bsk_im.where(bsk_im.eq(1.0), 7)
  
    csa_im = csa_im.where(csa_im.eq(1.0), 8)
    csb_im = csb_im.where(csb_im.eq(1.0), 9)
    csc_im = csc_im.where(csc_im.eq(1.0), 10)
    #csd not present
    cwa_im = cwa_im.where(cwa_im.eq(1.0), 11)
    cwb_im = cwb_im.where(cwb_im.eq(1.0), 12)
    cwc_im = cwc_im.where(cwc_im.eq(1.0), 13)
    #cwd not present
    cfa_im = cfa_im.where(cfa_im.eq(1.0), 14)
    cfb_im = cfb_im.where(cfb_im.eq(1.0), 15)
    cfc_im = cfc_im.where(cfc_im.eq(1.0), 16)
    #cfd not present
  
    dsa_im = dsa_im.where(dsa_im.eq(1.0), 17)
    dsb_im = dsb_im.where(dsb_im.eq(1.0), 18)
    dsc_im = dsc_im.where(dsc_im.eq(1.0), 19)
    dsd_im = dsd_im.where(dsd_im.eq(1.0), 20)
    dwa_im = dwa_im.where(dwa_im.eq(1.0), 21)
    dwb_im = dwb_im.where(dwb_im.eq(1.0), 22)
    dwc_im = dwc_im.where(dwc_im.eq(1.0), 23)
    dwd_im = dwd_im.where(dwd_im.eq(1.0), 24)
    dfa_im = dfa_im.where(dfa_im.eq(1.0), 25)
    dfb_im = dfb_im.where(dfb_im.eq(1.0), 26)
    dfc_im = dfc_im.where(dfc_im.eq(1.0), 27)
    dfd_im = dfd_im.where(dfd_im.eq(1.0), 28)
  
    et_im = et_im.where(et_im.eq(1.0), 29)
    ef_im = ef_im.where(ef_im.eq(1.0), 30)
  
    type_ic = ee.ImageCollection([af_im, am_im, aw_im, bwh_im, bwk_im, bsh_im, bsk_im, csa_im, csb_im, csc_im, cwa_im, cwb_im, cwc_im, cfa_im, cfb_im, cfc_im, dsa_im, dsb_im, dsc_im, dsd_im, dwa_im, dwb_im, dwc_im, dwd_im, dfa_im, dfb_im, dfc_im, dfd_im, et_im, ef_im])
  
    def change_band_name_fn(im):
      bLabel = im.bandNames().get(0)
      return im.select([bLabel],['B1'])
  
    type_ic = ee.ImageCollection(type_ic.map(change_band_name_fn))
    type_ic = ee.ImageCollection(type_ic.cast({'B1':'int64'}, ['B1']))
    type_im = type_ic.reduce(ee.Reducer.sum())
  
    return type_im

  @staticmethod
  def download(type_image=None, geo=None, scale=None, file_name='KG_map'):
    """
    Spawns a download task to Google Drive in geotif format. Download progress may be monitored in the Earth Engine Online Code Editor.

    Parameters
    ----------
    type_im : ee.Image
              Classified image.
    geo : ee.Geometry
          Bounding box geometry (from ee.Geometry.BBox).
    scale : float
            Scale/resolution of downloaded image.
    filename : string
               Downloaded file name.

    Returns
    -------
    None
    
    Notes
    -----
    - Assumes WGS84 coordinate system.
    - Assumes overlapping input images that exist only within selected hemisphere.
    """
    type_im = type_image.toDouble()
    task = ee.batch.Export.image.toDrive(
      image=type_im,
      description=file_name,
      region=geo,
      scale=scale,
      crs='EPSG:4326',
      maxPixels=1e13)
    task.start()

  @staticmethod
  def get_vis_params():
    """
    Visualization parameters for use with geemap.

    Parameters
    ----------
    None
    
    Returns
    -------
    dict of visualization parameters including the minimum value (1), maximum value (30), and a commonly used color scheme for KGCC. 
    
    Notes
    -----
    -Only needed when visualizing with geemaps.
    """
    typePalette = [
      '#0000FF', '#0078FF', '#46AAFA', '#FF0000', '#FF9696', '#F5A500', '#FFDC64',
      '#FFFF00', '#C8C800', '#969600', '#96FF96', '#64C864', '#329632',
      '#C8FF50', '#64FF50', '#32C800', '#FF00FF', '#C800C8', '#963296', '#966496',
      '#AAAFFF', '#5A78DC', '#4B50B4', '#320087', '#00FFFF', '#37C8FF', '#007D7D', '#00465F',
      '#B2B2B2', '#666666']
    return {'min':1, 'max':30, 'palette':typePalette}
  
  @staticmethod
  def get_class_index():
    """
    Look-up dictionary that relates class values to class names and letter labels.

    Parameters
    ----------
    None
    
    Returns
    -------
    dict of class values, class names, and letter labels.
    """
    typeLabels = [
      'Af - Tropical, Rainforest', 'Am - Tropical, Monsoon', 'Aw - Tropical, Savanna', 'Bwh - Arid, Desert, Hot', 'Bwk - Arid, Desert, Cold', 'Bsh - Semi-Arid, Steppe, Hot', 'Bsk - Semi-Arid, Steppe, Cold',
      'Csa - Temperate, Dry Summer, Hot Summer', 'Csb - Temperate, Dry Summer, Warm Summer', 'Csc - Temperate, Dry Summer, Cold Summer', 'Cwa - Temperate, Dry Winter, Hot Summer', 'Cwb - Temperate, Dry Winter, Warm Summer', 'Cwc - Temperate, Dry Winter, Cold Summer',
      'Cfa - Temperate, No Dry Season, Hot Summer', 'Cfb - Temperate, No Dry Season, Warm Summer', 'Cfc - Temperate, No Dry Season, Cold Summer', 'Dsa - Cold, Dry Summer, Hot Summer', 'Dsb - Cold, Dry Summer, Warm Summer', 'Dsc - Cold, Dry Summer, Cold Summer', 'Dsd - Cold, Dry Summer, Very Cold Winter',
      'Dwa - Cold, Dry Winter, Hot Summer', 'Dwb - Cold, Dry Winter, Warm Summer', 'Dwc - Cold, Dry Winter, Cold Summer', 'Dwd - Cold, Dry Winter, Very Cold Winter', 'Dfa - Cold, No Dry Season, Hot Summer', 'Dfb - Cold, No Dry Season, Warm summer', 'Dfc - Cold, No Dry season, Cold Summer', 'Dfd - Cold, No Dry Season, Very Cold Winter',
      'Et - Polar Tundra', 'Ef - Polar Ice Cap'] 
    return dict(zip(range(1, 31), typeLabels))
  
