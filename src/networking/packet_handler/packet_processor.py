from src.networking.packets.serverbound import KeepAlive as KeepAliveServerbound, TeleportConfirm
from src.networking.packets.clientbound import ChunkData, UnloadChunk, SpawnEntity, \
    DestroyEntities, KeepAlive, ChatMessage, PlayerPositionAndLook, TimeUpdate, \
    HeldItemChange, SetSlot, PlayerListItem

from src.networking.packets.clientbound import GameState as GameStateP


class PacketProcessor:

    # A packet processor processes packets and mutates the game state
    def __init__(self, game_state):
        self.game_state = game_state

    def destroy_entities(self, packet):
        destroy_entities = DestroyEntities().read(packet.packet_buffer)
        for entity_id in destroy_entities.Entities:
            if entity_id in self.game_state.entities:
                print("Removed entity ID: %s" % entity_id, self.game_state.entities.keys(),
                      flush=True)
                del self.game_state.entities[entity_id]  # Delete the entity

    def player_list(self, packet):
        player_list_item = PlayerListItem().read(packet.packet_buffer)

        add_player = 0
        remove_player = 4

        if player_list_item.Action == add_player or player_list_item.Action == remove_player:
            for player in player_list_item.Players:
                uuid = player[0]
                if player_list_item.Action == add_player:
                    self.game_state.player_list[uuid] = packet
                elif player_list_item.Action == remove_player:
                    if uuid in self.game_state.packet_log:
                        del self.game_state.player_list[uuid]

    def spawn_entity(self, packet):
        spawn_entity = SpawnEntity().read(packet.packet_buffer)
        if spawn_entity.EntityID not in self.game_state.entities:
            self.game_state.entities[spawn_entity.EntityID] = packet
            print("Added entity ID: %s" % spawn_entity.EntityID, self.game_state.entities.keys(),
                  flush=True)

    def chunk_unload(self, packet):
        unload_chunk = UnloadChunk().read(packet.packet_buffer)
        chunk_key = (unload_chunk.ChunkX, unload_chunk.ChunkY)
        if chunk_key in self.game_state.chunks:
            del self.game_state.chunks[chunk_key]
            print("UnloadChunk", unload_chunk.ChunkX, unload_chunk.ChunkY, flush=True)

    def chunk_load(self, packet):
        chunk_data = ChunkData().read(packet.packet_buffer)
        chunk_key = (chunk_data.ChunkX, chunk_data.ChunkY)
        if chunk_key not in self.game_state.chunks:
            self.game_state.chunks[chunk_key] = packet
            print("ChunkData", chunk_data.ChunkX, chunk_data.ChunkY, flush=True)

    # Processes a packet and returns a response packet if needed
    def process_packet(self, packet):
        if packet.id in self.game_state.join_ids:
            self.game_state.packet_log[packet.id] = packet
        elif packet.id == ChunkData.id:  # ChunkData
            self.chunk_load(packet)
        elif packet.id == UnloadChunk.id:  # UnloadChunk
            self.chunk_unload(packet)
        elif packet.id in SpawnEntity.ids:
            self.spawn_entity(packet)
        elif packet.id == DestroyEntities.id:
            self.destroy_entities(packet)
        elif packet.id == KeepAlive.id:  # KeepAlive Clientbound
            keep_alive = KeepAlive().read(packet.packet_buffer)
            print("Responded to KeepAlive", keep_alive, flush=True)
            return KeepAliveServerbound(KeepAliveID=keep_alive.KeepAliveID)
        elif packet.id == ChatMessage.id:
            chat_message = ChatMessage().read(packet.packet_buffer)
            print(chat_message, flush=True)
        elif packet.id == PlayerPositionAndLook.id:
            pos_packet = PlayerPositionAndLook().read(packet.packet_buffer)

            # Log the packet
            self.game_state.packet_log[packet.id] = packet

            # Send back a teleport confirm
            return TeleportConfirm(TeleportID=pos_packet.TeleportID)
        elif packet.id == TimeUpdate.id:
            self.game_state.packet_log[packet.id] = packet
        elif packet.id == HeldItemChange.id:
            self.game_state.held_item_slot = HeldItemChange().read(packet.packet_buffer).Slot
        elif packet.id == GameStateP.id:
            game_state = GameStateP().read(packet.packet_buffer)
            self.game_state.gs_reason = game_state.Reason
            self.game_state.gs_value = game_state.Value
        elif packet.id == SetSlot.id:
            set_slot = SetSlot().read(packet.packet_buffer)
            self.game_state.main_inventory[set_slot.Slot] = packet
        elif packet.id == PlayerListItem.id:
            self.player_list(packet)

        return None