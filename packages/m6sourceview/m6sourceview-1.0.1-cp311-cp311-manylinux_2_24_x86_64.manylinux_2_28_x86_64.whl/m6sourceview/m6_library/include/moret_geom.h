#ifdef __cplusplus
//....This is needed for C++, otherwise this header works only for C
extern "C" {
#endif

// @brief Set the pointers to external RNG procedures required by geometry procedures
//
// @param[in] external_set_rng_seed_geom           : pointer to a routine to set the seed of the random number generator for the geometry
// @param[in] external_setup_rng_geom              : pointer to a routine to setup the random number generator (take into account the seed and the initial index) for the geometry
// @param[in] external_rand_non_zero_geom          : pointer to a function to get a random number different from 0 for the geometry
// @param[in] external_rand_non_zero_non_one_geom  : pointer to a function to get a random number different from 0 and 1 for the geometry
extern void moret_set_geometry_ptr_to_external_rng_proc_c(void (*external_set_rng_seed_geom) (int&), void (*external_setup_rng_geom) (void), double (*external_rand_non_zero_geom) (void), double (*external_rand_non_zero_non_one_geom) (void));


// @brief Load the MORET geometry
//
// @param[in]    overlapping_volumes_test          : true if the test of overlapping volumes must be done
// @param[out]   warnings                          : true if there are warning messages during the loading of the moret geometry
// @param[in]    input_data_file_complete_name     : complete name of the input data file
// @param[inout] position_in_input_data_file       : position reached in the input data file
extern void moret_read_geometry_c(bool &overlapping_volumes_test, bool &warnings, char *input_data_file_complete_name, long &position_in_input_data_file);


// requests relative to the geometry

// @brief Get the number of modules in the geometry
extern int moret_get_modules_number_c();

// @brief Get the number of primary volumes in the geometry
extern int moret_get_primary_volumes_number_c();

// @brief Get the number of holes in the geometry (can be zero)
extern int moret_get_holes_number_c();

// @brief Get the number of volumes in the geometry
extern int moret_get_volumes_number_c();

// @brief Get the number of media in the geometry
extern int moret_get_media_number_c();

// @brief Get the number of external faces of the geometry
extern int moret_get_external_faces_number_c();

// @brief Indicate if the external volume is delimited (limits known)
extern bool moret_is_external_volume_delimited_c();

// @brief Minimum space coordinates of the external volume
//
// @param[inout] coord[3] :  minimum space coordinates of the external volume
extern void moret_get_minimum_coord_c(double coord[3]); 

// @brief Maximum space coordinates of the external volume
//
// @param[inout] coord[3] :  maximum space coordinates of the external volume
extern void moret_get_maximum_coord_c(double coord[3]); 

// @brief Indicate if simple-shape bounding volumes are available in the geometry library
extern bool moret_are_bounding_volumes_available_c();

// @brief Lecture des options du mot-cle WOOD
// Lecture du mot-cle LEAR et de ses options
// Appel de la routine d'initialisation
extern void moret_read_woodcock_geometry_c();

// @brief Get the number of Woodcock modules
extern int moret_get_woodcock_modules_number_c();

// @brief Indicate if the Woodcock learning is to save
extern bool moret_is_woodcock_learning_to_save_c();

// @brief Sauvegarde des donnees apprises
extern void moret_save_woodcock_learning_c();


// requests relative to a module

// @brief Get the name of the module
//
// @param[in]    index       :  index of the module (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the module
// @param[inout] name        :  name of the module if length sufficient (optional)
extern void moret_get_module_name_c(int &index, int &name_length, char *name);

// @brief Indicate if the module is used
//
// @param[in] index :  index of the module (consecutive numbering starting from 1)
extern bool moret_is_module_used_c(int &index);

// @brief Get the list of indices of (non fictive) primary volumes which belong to the module
//
// @param[in]    module_index   : index of the module (consecutive numbering starting from 1)
// @param[inout] nb_vol         : number of primary volumes in the module
// @param[inout] list_vol       : list of indices of (non fictive) primary volumes in the module if size of array is sufficient (optional)
extern void moret_get_list_primary_vol_of_module_c(int &module_index, int &nb_vol, int *list_vol);


// requests relative to a primary volume

// @brief Get the name of the primary volume
//
// @param[in]    index       :  index of the primary volume (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the primary volume
// @param[inout] name        :  name of the primary volume if length sufficient (optional)
extern void moret_get_primary_volume_name_c(int &index, int &name_length, char *name);

// @brief Get the medium index of the primary volume
//
// @param[in] index :  index of the primary volume (consecutive numbering starting from 1)
extern int moret_get_primary_volume_medium_c(int &index);

// @brief Get the name of the type of the primary volume
//
// @param[in]    index       :  index of the primary volume (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the type of the primary volume
// @param[inout] name        :  name of the type of the primary volume if length sufficient (optional)
extern void moret_get_primary_volume_type_name_c(int &index, int &name_length, char *name);

// @brief Get the short name of the shape of the primary volume
//
// @param[in]    index       :  index of the primary volume (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the short name of the form of the primary volume
// @param[inout] name        :  name of the short name of the form of the primary volume if length sufficient (optional)
extern void moret_get_primary_volume_shape_short_name_c(int &index, int &name_length, char *name);


// requests relative to a hole

// @brief Get the name of the hole
//
// @param[in]    index       :  index of the hole (consecutive numbering starting from 0)
// @param[inout] name_length :  length of the name of the hole
// @param[inout] name        :  name of the hole if length sufficient (optional)
// @param[in]    last_level  :  false by default, i.e. all the levels - if true only the last level (optional)
extern void moret_get_hole_name_c(int &index, int &name_length, char *name, bool* last_level);

// @brief Get the index of the module filling the hole
//
// @param[in] index :  index of hole
extern int moret_get_module_filling_hole_c(int &index);

// @brief Get the list of indices of volumes which belong to the hole
//
// @param[in]    hole_index   : index of the hole (consecutive numbering starting from 0)
// @param[inout] nb_vol       : number of volumes in the hole
// @param[inout] list_vol     : list of indices of volumes in the hole if size of array is sufficient (optional)
extern void moret_get_list_vol_of_hole_c(int &hole_index, int &nb_vol, int *list_vol);


// requests relative to a volume

// @brief Get the name of the volume
//
// @param[in]    index       :  index of the volume (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the volume
// @param[inout] name        :  name of the volume if length sufficient (optional)
// @param[in]    last_level  :  false by default, i.e. all the levels - if true only the last level (optional)
extern void moret_get_volume_name_c(int &index, int &name_length, char *name, bool* last_level);

// @brief Get the short name of the volume
//
// @param[in]    index       :  index of the volume (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the short name of the volume
// @param[inout] name        :  short name of the volume if length sufficient (optional)
extern void moret_get_volume_short_name_c(int &index, int &name_length, char *name);

// @brief Get the index of the real volume associated to the volume - different if the volume is not created by the user
//
// @param[in] index   : index of the volume (consecutive numbering starting from 1)
extern int moret_get_real_volume_associated_c(int &index);

// @brief Get the index of the medium of the volume
//
// @param[in] index :  index of the volume (consecutive numbering starting from 1)
extern int moret_get_volume_medium_c(int &index);

// @brief Get the index of the hole which contains the volume
//
// @param[in] index :  index of the volume (consecutive numbering starting from 1)
extern int moret_get_hole_containing_vol_c(int &index);

// @brief Indicate if the volume is a void volume (outside the geometry)
//
// @param[in] index :  index of the volume (any value)
extern bool moret_is_void_volume_c(int &index);

// @brief Indicate if the volume is virtual (volume which is used to intersect other volumes)
//
// @param[in] index :  index of the volume (consecutive numbering starting from 1)
extern bool moret_is_virtual_volume_c(int &index);

// @brief Indicate if the volume is to exclude (no score to calculate):
// - virtual volume (volume which is used to intersect other volumes)
// - fictive mesh volume (scores are calculated for the lattice volume)
// - volume occulted by a volume contained with same shape and dimensions
//
// @param[in] index :  index of the volume (consecutive numbering starting from 1)
extern bool moret_is_excluded_volume_c(int &index);

// @brief Get a simple-shape bounding volume of a given volume of the geometry
//
// @param[in]    volume_index         : index of the volume (consecutive numbering starting from 1)
// @param[out]   shape                : shape of the bounding volume (1: box, 2: sphere, 3: x-oriented cylinder, 4: y-oriented cylinder, 5: z-oriented cylinder, 7: ellipsoid)
// @param[inout] center_coord[3]      : space coordinates of the simple-shape bounding volume
// @param[inout] half_dim[3]          : half dimensions of the simple-shape bounding volume
// @param[out]   is_rotated           : true if the simple-shape bounding volume is rotated with respect to the main axes of the geometry
// @param[inout] rotation_matrix[3,3] : rotation matrix to calculate the coordinates with respect to the main axes of the geometry
// @param[out]   error                : true if no bounding volume could be determined
extern void moret_get_bounding_volume_c(int &volume_index, int &shape, double center_coord[3], double half_dim[3], bool &is_rotated, double rotation_matrix[3][3], bool &error);

// @brief Get the minimum and maximum space coordinates of a given volume of the geometry
//
// @param[in]    volume_index         : index of the volume (consecutive numbering starting from 1)
// @param[inout] min_coord[3]         : minimum space coordinates of the volume
// @param[inout] max_coord[3]         : maximum space coordinates of the volume
extern void moret_get_min_max_coord_of_volume_c(int &volume_index, double min_coord[3], double max_coord[3]);


// requests relative to a Woodcock module

// @brief Get the name of the of Woodcock module
//
// @param[in]    index       :  index of the Woodcock module (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the Woodcock module
// @param[inout] name        :  short name of the Woodcock module if length sufficient (optional)
extern void moret_get_woodcock_module_name_by_index_c(int &index, int &name_length, char *name);

// @brief Get the list of media present in a Woodcock module
//
// @param[in]    index      :  index of the Woodcock module (consecutive numbering starting from 1)
// @param[inout] nb_media   :  number of media in the Woodcock module
// @param[inout] list_media :  list of indices of media in the Woodcock module if size of array is sufficient (optional)
extern void moret_get_list_of_media_in_woodcock_module_by_index_c(int &index, int &nb_media, int *list_media);


// requests relative to a volume and a point

// @brief Get the coordinates of a point in the global geometry, knowing the volume in which it is located and the coordinates of the point in the local frame in which the volume is described
//
// @param[in]  volume_index       : index of the volume (consecutive numbering starting from 1)
// @param[in]  local_coord[3]     : local coordinates of a point located in the volume
// @param[out] global_coord[3]    : coordinates of the point in the global geometry
extern void moret_convert_point_from_user_to_global_c(int &volume_index, double local_coord[3], double global_coord[3]);

// @brief Test if a point belongs to a given volume
//
// @param[in] volume_index            : index of the volume (consecutive numbering starting from 1)
// @param[in] coord[3]                : space coordinates of the point in the global geometry
// @param[in] tolerance               : tolerance (optional, zero by default)
// @param[in] multilevel_interaction  : true by default - if false, allow testing if a point belongs to a volume without taking into account the interaction of volumes with holes and lattices containing the volume (optional)
// @param[in] fictive_volume_excluded : true by default - if false, allow testing if a point belongs to a volume, taking into account the fictive volumes inside the tested volume which may contain the point
extern bool moret_does_point_belong_to_volume_c(int &volume_index, double coord[3], double* tolerance, bool* multilevel_interaction, bool* fictive_volume_excluded);


// requests relative to a point or a vector

// @brief Apply the rotation matrix to the input vector
//
// @param[in]  rotation_matrix[3,3] : rotation matrix
// @param[in]  input[3]             : input vector
// @param[out] output[3]            : output vector
extern void moret_rotation_c(double rotation_matrix[3][3], double input[3], double output[3]);


// requests relative to a medium

// @brief Get the name of the medium
//
// @param[in]    index       :  index of the medium (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the medium
// @param[inout] name        :  name of the medium if length sufficient (optional)
extern void moret_get_medium_name_c(int &index, int &name_length, char *name);

// @brief Get the index of the medium given its name
//
// @param[in] name :  name of the medium
extern int moret_get_medium_index_c(char *name);

// @brief Indicate if the medium is used
//
// @param[in] index :  index of the medium (consecutive numbering starting from 1)
extern bool moret_is_medium_used_c(int &index);

// @brief Indicate if the medium is a random medium
//
// @param[in] index :  index of the medium (consecutive numbering starting from 1)
extern bool moret_is_random_medium_c(int &index);

// @brief Get the index of the random medium if the medium is a random medium
//
// @param[in] index :  index of the medium (consecutive numbering starting from 1)
extern int moret_get_random_medium_index_c(int &index);

// @brief Get the list of indices of the standard media in the random medium
//
// @param[in]    rand_medium_index : index of the random medium (consecutive numbering starting from 1)
// @param[inout] nb_media          : number of of standard media in the random medium
// @param[inout] list_media        : list of indices of standard media in the random medium if size of array is sufficient (optional)
extern void moret_get_list_media_of_random_medium_c(int &rand_medium_index, int &nb_media, int *list_media);


// requests relative to an external face

// @brief Get the name of the external face
//
// @param[in]    index       :  index of the external face (consecutive numbering starting from 1)
// @param[inout] name_length :  length of the name of the external face
// @param[inout] name        :  name of the external face if length sufficient (optional)
extern void moret_get_external_face_name_c(int &index, int &name_length, char *name);

// @brief Check the face specified for boundary condition, get the face index and return an error if the face is unknown or if it cannot be applied boundary condition
//
// @param[in]  name    : name of the face specified for boundary condition
// @param[out] index   : index of the face
extern void moret_check_face_for_boundary_condition_c(char *name, int &index);

// @brief Get the index of the external volume associated to the external face
//
// @param[in] external_face_index :  index of the external face (consecutive numbering starting from 1)
extern int moret_get_volume_index_associated_to_external_face_c(int &external_face_index);

// @brief Get the face index of the external volume associated to the external face
//
// @param[in] external_face_index :  index of the external face (consecutive numbering starting from 1)
extern int moret_get_face_index_associated_to_external_face_c(int &external_face_index);


// requests relative to the tracking

// @brief Actualize the space coordinates and the calculated distances used for the geometry tracking after a specified track length
//
// @param[in] track_length       : track length
extern void moret_actualize_coord_distances_c(double &track_length);

// @brief Get the space coordinates used for the geometry tracking
//
// @param[inout] coord[3]       : space coordinates
extern void moret_get_coord_c(double coord[3]);

// @brief Get the direction cosines used for the geometry tracking
//
// @param[inout] cos_dir[3]       : direction cosines
extern void moret_get_cos_dir_c(double cos_dir[3]);

// @brief Get the index of the current volume used for the geometry tracking
extern int moret_get_current_volume1_c();

// @brief Refresh and get the index of the current volume
extern int moret_refresh_and_get_current_volume_c();

// @brief Set the current position and get the index of the current volume used for the geometry tracking
//
// @param[in] coord[3]                           : space coordinates
extern int moret_get_current_volume2_c(double coord[3]);

// @brief Indicate if the Woodcock tracking is activated
extern bool moret_is_woodcock_tracking_activated_c();

// @brief Indicate if the Woodcock tracking is active in the current position
extern bool moret_is_woodcock_tracking_active_c();

// @brief Get the Woodcock module index in the current position
extern int moret_get_woodcock_module_index_c();

// @brief Set the data used for the geometry tracking
//
// @param[in] coord[3]                        : space coordinates
// @param[in] cos_dir[3]                      : direction cosines
// @param[in] current_volume_index            : index of the current volume (optional)
// @param[in] woodcock_tracking_deactivated   : woodcock tracking deactivated or not (optional)
extern void moret_set_tracking_c(double coord[3], double cos_dir[3], int *current_volume_index, bool *woodcock_tracking_deactivated);

// @brief Set the position used for the geometry tracking
//
// @param[in] coord[3]                        : space coordinates
// @param[in] current_volume_index            : index of the current volume (optional)
// @param[in] woodcock_tracking_deactivated   : woodcock tracking deactivated or not (optional)
extern void moret_set_tracking_position_c(double coord[3], int *current_volume_index, bool *woodcock_tracking_deactivated);

// @brief Set the direction used for the geometry tracking and reset the tracking status if the contrary is not specified
//
// @param[in] cos_dir[3]                      : direction cosines
// @param[in] reset_status                    : indicate if the status must be reset - true by default - false to not forget the history and return to the left volume (optional)
extern void moret_set_tracking_direction_c(double cos_dir[3], bool *reset_status);

// @brief Get the index of the current medium used for the geometry tracking
extern int moret_get_current_medium_c();

// @brief Set the data used for the geometry tracking and get the distance to the next interface
//
// @param[in] coord[3]                        : space coordinates
// @param[in] cos_dir[3]                      : direction cosines
// @param[in] current_volume_index            : index of the current volume (optional)
// @param[in] woodcock_tracking_deactivated   : woodcock tracking deactivated or not (optional)
extern double moret_get_distance_to_next_interface1_c(double coord[3], double cos_dir[3], int *current_volume_index, bool *woodcock_tracking_deactivated);

// @brief Get the distance to the next interface, using the data already set
extern double moret_get_distance_to_next_interface2_c();

// @brief Set the data used for the geometry tracking, determine the distance to the next interface and get the index of the volume after the next interface
//
// @param[in] coord[3]                        : space coordinates
// @param[in] cos_dir[3]                      : direction cosines
// @param[in] current_volume_index            : index of the current volume (optional)
// @param[in] woodcock_tracking_deactivated   : woodcock tracking deactivated or not (optional)
extern int moret_get_volume_after_next_interface1_c(double coord[3], double cos_dir[3], int *current_volume_index, bool *woodcock_tracking_deactivated);

// @brief Determine the index of the volume after the next interface, using the data already set.
// Must be called after:
// - the calculation of the distance to the next interface in the routine moret_get_distance_to_next_interface1_c or moret_get_distance_to_next_interface2_c,
// - the actualization of the space coordinates and the calculated distances in the routine moret_actualize_coord_distances_c.
extern int moret_get_volume_after_next_interface2_c();

// @brief Cross the current volume in the current trajectory: get the index of the crossed volume and the distance through the volume
//
// @param[out] volume_index    : index of the volume
// @param[out] distance        : distance through the volume
// @param[out] exit            : true if the trajectory exits the geometry
extern void moret_get_distance_through_current_volume_c(int &volume_index, double &distance, bool &exit);

// @brief Get the index of the exited volume
extern int moret_get_exit_volume_c();

// @brief Get the index of the exit face of the exited volume
extern int moret_get_exit_face_c();

// @brief Get the components of the normal vector on the exit face of the external volume
//
// @param[inout] normal_vector[3]   : components of the normal vector on the exit face of the external volume
extern void moret_get_normal_vector_c(double normal_vector[3]);

// @brief Save the tracking data
//
// @param[in] nb_times       : number of copies to realize
extern void moret_save_tracking_data_c(int &nb_times);

// @brief Retrieve the last tracking data
extern void moret_retrieve_tracking_data_c();

#ifdef __cplusplus
}
#endif
