
set(FLATC_EXECUTABLE $<TARGET_FILE:flatc>)

set(FLATBUFFER_SCHEMAS
  ${FB_SCHEMA_DIR}/deb_type.fbs  
)

foreach(fbs_file ${FLATBUFFER_SCHEMAS})
  get_filename_component(fname ${fbs_file} NAME_WE)
  set(generated_header ${FB_SCHEMA_DIR}/${fname}_gen.h)

  add_custom_command(
    OUTPUT ${generated_header}
    COMMAND ${FLATC_EXECUTABLE} --cpp -o ${FB_SCHEMA_DIR} ${fbs_file}
    COMMAND ${CMAKE_COMMAND} -E rename
            ${FB_SCHEMA_DIR}/${fname}_generated.h
            ${generated_header}
    DEPENDS ${fbs_file}
    COMMENT "Generating cpp flatbuffer from ${fbs_file}"
  )

  list(APPEND GENERATED_HEADERS ${generated_header})
endforeach()

add_custom_target(generate_flatbuffers ALL DEPENDS ${GENERATED_HEADERS})
