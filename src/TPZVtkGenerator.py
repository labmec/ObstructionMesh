"""
class to generate VTK files from Gmsh meshes

Created by Carlos @ 09/15/2025
"""
from src.TPZBasicDataStructure import TPZBasicDataStructure
class TPZVtkGenerator(TPZBasicDataStructure):
    def __init__(self):
        self.fPhysicalNames: list[dict] = []
        self.fEntities: dict[str, list[dict]] = {
            "nodes": [],
            "curves": [],
            "surfaces": [],
            "volumes": []
        }
        self.fNodes: list[dict] = []
        self.fElements: list[dict] = []

        return

    def ParsePhysicalNames(self, physicalLines:list[str]) -> None:
        """
        Parse the physical names from the mesh file

        inputs:
            physicalLines: lines containing the physical names
        """
        nPhysical = int(physicalLines[0])

        for line in physicalLines[1:]:
            dim, tag, name = line.split()
            self.fPhysicalNames.append({
                "dim": int(dim),
                "tag": int(tag),
                "name": name.strip()
            })

        if len(self.fPhysicalNames) != nPhysical:
            self.DebugStop(f"Expected {nPhysical} physical entities, but found {len(self.fPhysicalNames)}")

        return

    def FindNodes(self, nodes:list[dict], nodeLines:list[str]) -> None:
        """
        Find nodes in the mesh file

        inputs:
            nodeLines: lines containing the nodes data
        """
        for nodeLine in nodeLines:
            nodeInfo = nodeLine.split()

            nodeTagIdx = 0
            nodeTag = int(nodeInfo[nodeTagIdx])
            
            coordIdx = nodeTagIdx + 1
            x, y, z = nodeInfo[coordIdx : coordIdx + 3]

            numPGIdx = coordIdx + 3
            nodeNumPhysicalGroups = int(nodeInfo[numPGIdx])

            physicalGroups = []
            for physicalGroup in nodeInfo[numPGIdx + 1:]:
                physicalGroups.append(int(physicalGroup))

            nodes.append({
                "tag": nodeTag,
                "x": float(x),
                "y": float(y),
                "z": float(z),
                "numPhysicalGroups": nodeNumPhysicalGroups,
                "physicalGroups": physicalGroups
            })

        return

    def FindEntities(self, entity:list[dict], entityLines:list[str]) -> None:
        """
        Find entities with one, two or three dimensional entities.
        inputs:
            entity: list to store the entities found
            entityLines: lines containing the entities data
        """
        for line in entityLines:
            entityInfo = line.split()

            entityTagIdx = 0
            entityTag = int(entityInfo[entityTagIdx])

            numPGIdx = 7
            entityNumPhysicalGroups = int(entityInfo[numPGIdx])

            physicalGroups = []
            physicalGroupIdx = numPGIdx + 1
            for physicalGroup in entityInfo[physicalGroupIdx : (physicalGroupIdx + entityNumPhysicalGroups)]:
                physicalGroups.append(int(physicalGroup))

            boundaryTags = []
            nBoundary = int(entityInfo[physicalGroupIdx + len(physicalGroups)])
            for boundaryTag in entityInfo[physicalGroupIdx + len(physicalGroups) + 1:]:
                boundaryTag = int(boundaryTag)
                boundaryTag = -boundaryTag if boundaryTag < 0 else boundaryTag

                boundaryTags.append(boundaryTag)

            entity.append({
                "tag": entityTag,
                "numPhysicalGroups": entityNumPhysicalGroups,
                "physicalGroups": physicalGroups,
                "numBoundary": nBoundary,
                "boundaryTags": boundaryTags
            })

        return

    def ParseEntities(self, entityLines: list[str]) -> None:
        """
        Parse the entities from the mesh file
        inputs:
            entityLines: lines containing the entities data
        """
        nNodes, nCurves, nSurfaces, nVolumes = entityLines[0].split()    

        nodesStart = 1
        nodesEnd = nodesStart + int(nNodes)

        curvesStart = nodesEnd
        curvesEnd = curvesStart + int(nCurves)

        surfacesStart = curvesEnd
        surfacesEnd = surfacesStart + int(nSurfaces)

        volumesStart = surfacesEnd

        self.FindNodes(self.fEntities['nodes'], entityLines[nodesStart: nodesEnd])
        self.FindEntities(self.fEntities['curves'], entityLines[curvesStart: curvesEnd])
        self.FindEntities(self.fEntities['surfaces'], entityLines[surfacesStart: surfacesEnd])
        self.FindEntities(self.fEntities['volumes'], entityLines[volumesStart:])

        if len(self.fEntities['nodes']) != int(nNodes):
            self.DebugStop(f"Expected {nNodes} nodes, but found {len(self.fEntities['nodes'])}")

        if len(self.fEntities['curves']) != int(nCurves):
            self.DebugStop(f"Expected {nCurves} curves, but found {len(self.fEntities['curves'])}")

        if len(self.fEntities['surfaces']) != int(nSurfaces):
            self.DebugStop(f"Expected {nSurfaces} surfaces, but found {len(self.fEntities['surfaces'])}")

        if len(self.fEntities['volumes']) != int(nVolumes):
            self.DebugStop(f"Expected {nVolumes} volumes, but found {len(self.fEntities['volumes'])}")

        return

    def ParseNodes(self, nodeLines: list[str]) -> None:
        """
        Parse the nodes from the mesh file
        inputs:
            nodeLines: lines containing the node data
        """
        _, nNodes, minTag, maxTag = nodeLines[0].split()

        i = 1
        nodeTagIdxList = []
        coordsIdxList = []
        for i, line in enumerate(nodeLines[1:], start=1):
            if len(line.split()) == 1:
                nodeTagIdxList.append((i, line))
            elif len(line.split()) == 3:
                coordsIdxList.append((i, line))
            
        for nodeTag, coord in zip(nodeTagIdxList, coordsIdxList):
            x, y, z = map(float, coord[1].split())
            
            self.fNodes.append({
                "tag": int(nodeTag[1]),
                "x": x,
                "y": y,
                "z": z
            })

        if len(self.fNodes) != int(nNodes):
            self.DebugStop(f"Expected {nNodes} nodes, but found {len(self.fNodes)}")

        if int(minTag) != self.fNodes[0]['tag']:
            self.DebugStop(f"Expected minimum node tag to be {minTag}, but found {self.fNodes[0]['tag']}")

        if int(maxTag) != self.fNodes[-1]['tag']:
            self.DebugStop(f"Expected maximum node tag to be {maxTag}, but found {self.fNodes[-1]['tag']}")

        return

    def ParseElements(self, elementLines: list[str]) -> None:
        """
        Parse the elements from the mesh file
        inputs:
            elementLines: lines containing the element data
        """
        i = 1
        while i < len(elementLines) - 1:
            elementLine = elementLines[i].split()

            if len(elementLine) != 4:
                i += 1
                continue

            elDim, elEntityTag, elType, numElBlock = map(int, elementLine)

            for _ in elementLines[i + 1 : i + 1 + numElBlock]:
                elementTag, *nodeTags = map(int, _.split())

                self.fElements.append({
                    "tag": elementTag,
                    "dim": elDim,
                    "type": elType,
                    "nodeTags": nodeTags,
                    "entityTag": elEntityTag
                })

            i += 1 + numElBlock
                
        return

    def MergeEntityAndElements(self) -> None:
        """
        Merge the entities and elements data
        """
        for element in self.fElements:
            elEntityTag = element['entityTag']
            elDim = element['dim']

            if elDim == 0:
                entityList = self.fEntities['nodes']
            
            elif elDim == 1:
                entityList = self.fEntities['curves']
            
            elif elDim == 2:
                entityList = self.fEntities['surfaces']
            
            elif elDim == 3:
                entityList = self.fEntities['volumes']

            element['physicalGroups'] = next(e['physicalGroups'] for e in entityList if e['tag'] == elEntityTag)

        return

    def WriteVTKPointData(self) -> None:
        """
        Write the points data in VTK format
        """
        pointData = ""

        point = 0
        for node in self.fNodes:
            pointData += f"{node['x']} {node['y']} {node['z']}\n"
            point += 1

        return f"POINTS {point} double \n" + pointData + "\n"

    def WriteVTKCellData(self) -> None:
        """
        Write the cell data in VTK format
        """
        cellData = ""

        nCells, totalNumIndices = 0, 0
        for element in self.fElements:
            for _ in element['physicalGroups']:
                nNodes = len(element['nodeTags'])

                cellData += f"{nNodes}" 
                for nodeTag in element['nodeTags']:
                    cellData += f" {nodeTag - 1}"  # VTK uses zero-based indexing
                cellData += "\n"

                nCells += 1
                totalNumIndices += nNodes

        return f"CELLS {nCells} {totalNumIndices + nCells}\n" + cellData + "\n"

    def WriteVTKCellTypes(self) -> None:
        """
        Write the cell types in VTK format
        """
        mshToVtk = {
            1 : 3, # 2 node line
            2 : 5, # 3 node triangle
            3 : 9, # 4 node quadrangle
            4 : 10, # 4 node tetrahedron
            5 : 12, # 8 node hexahedron
            7 : 14, # 5 node pyramid 
        } 

        cellTypes = ""
        nTypes = 0
        for element in self.fElements:
            for _ in element['physicalGroups']:
                vtkType = element['type']

                cellTypes += f"{mshToVtk[vtkType]}\n"
                nTypes += 1

        return f"CELL_TYPES {nTypes}\n" + cellTypes + "\n"

    def nSolutions(self, field:str) -> int:
        """
        Return the number of solutions for a given field. Implement more if needed
        inputs:
            field: name of the field (e.g., "MaterialID")
        """
        if field == "MaterialID": return 1, "SCALARS"
        else: self.DebugStop(f"Field '{field}' not recognized")

    def Solution(self, field:str) -> str:
        """
        Return the solution data for a given field. Implement more if needed
        inputs:
            field: name of the field (e.g., "MaterialID")
        """
        fieldData = ""
        if field == "MaterialID":
            nElements = 0
            for element in self.fElements:
                for physicalGroup in element['physicalGroups']:
                    fieldData += f"{physicalGroup}\n"
                    nElements += 1

        return fieldData, nElements

    def WriteVTKHeader(self, fields: list[str]) -> None:
        """
        Write the VTK header
        """
        for field in fields:
            fieldSize, fieldType = self.nSolutions(field)
            fieldData, nElements = self.Solution(field)

            text = f"CELL_DATA {nElements}\n"
            text += f"{fieldType} MaterialID int {fieldSize}\n"
            text += "LOOKUP_TABLE default\n"
            text += f"{fieldData}"

        return text 

    def WriteVTK(self, vtkFileName: str, fields: list[str]) -> None:
        """
        Write the VTK file
        inputs:
            vtkFileName: name of the output VTK file (without extension)
            fields: list of fields to be included in the VTK file (e.g., ["MaterialID"])
        """
        text = "# vtk DataFile Version 2.0\n"
        text += "Created by Gmsh 4.13.1\n"
        text += "ASCII\n"
        text += "DATASET UNSTRUCTURED_GRID\n"

        text += self.WriteVTKPointData()

        text += self.WriteVTKCellData()

        text += self.WriteVTKCellTypes()

        text += self.WriteVTKHeader(fields)

        with open(f"{vtkFileName}.vtk", "w") as f:
            f.write(text)

        return

    def Do(self, outputFile: str, meshFile: str, fields: list[str]) -> None:
        """
        Main method to generate the VTK file from a Gmsh mesh file

        inputs:
            outputFile: name of the output file (without extension)
            meshFile: name of the Gmsh mesh file (with extension)
            fields: list of fields to be included in the VTK file (e.g., ["MaterialID"])
        """
        with open(meshFile, "r") as f:
                lines = f.readlines()

        physicalNamesStart = lines.index("$PhysicalNames\n")
        physicalNamesEnd = lines.index("$EndPhysicalNames\n")

        entitiesStart = lines.index("$Entities\n")
        entitiesEnd = lines.index("$EndEntities\n")

        nodesStart = lines.index("$Nodes\n")
        nodesEnd = lines.index("$EndNodes\n")

        elementsStart = lines.index("$Elements\n")
        elementsEnd = lines.index("$EndElements\n")

        self.ParsePhysicalNames(lines[physicalNamesStart + 1: physicalNamesEnd])
        self.ParseEntities(lines[entitiesStart + 1: entitiesEnd])
        self.ParseNodes(lines[nodesStart + 1: nodesEnd])
        self.ParseElements(lines[elementsStart + 1: elementsEnd])

        self.MergeEntityAndElements()

        self.WriteVTK(outputFile, fields)

        return